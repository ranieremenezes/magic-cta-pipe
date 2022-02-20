#!/usr/bin/env python
# coding: utf-8

"""
Author: Yoshiki Ohtani (ICRR, ohtani@icrr.u-tokyo.ac.jp)

This script processes MAGIC calibrated data (*_Y_*.root) with the MARS-like cleaning method and computes
the DL1 parameters (i.e., Hillas, timing and leakage parameters). The script saves an event in an output file
only when it reconstructs all the DL1 parameters. The telescope IDs are reset to the following values when saving
to the file for the convenience of the combined analysis with LST-1, whose telescope ID is 1:
MAGIC-I: tel_id = 2,  MAGIC-II: tel_id = 3

The MAGICEventSource module searches for all the sub-run files belonging to the same observation ID and stored in
the same directory of an input sub-run file. The module reads drive reports from the files and uses the information
to reconstruct the telescope pointing direction. Thus, it is best to store the files in the same directory.
If one gives the "--process-run" argument, the module also processes all the files together with the input file.

Usage:
$ python magic_data_cal_to_dl1.py
--input-file ./data/calibrated/20201216_M1_05093711.001_Y_CrabNebula-W0.40+035.root
--output-dir ./data/dl1
--config-file ./config.yaml
"""

import time
import yaml
import logging
import argparse
import warnings
import numpy as np
from pathlib import Path
from astropy import units as u
from ctapipe.io import HDF5TableWriter
from ctapipe.core import Container, Field
from ctapipe.image import (
    number_of_islands,
    hillas_parameters,
    timing_parameters,
    leakage_parameters,
)
from ctapipe.instrument import SubarrayDescription
from ctapipe_io_magic import MAGICEventSource
from magicctapipe.image import MAGICClean

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

warnings.simplefilter('ignore')

sec2nsec = 1e9

tel_positions = {
    2: u.Quantity([39.3, -62.55, -0.97], u.m),    # MAGIC-I
    3: u.Quantity([-31.21, -14.57, 0.2], u.m),    # MAGIC-II
}

pedestal_types = [
    'fundamental',
    'from_extractor',
    'from_extractor_rndm',
]

__all__ = [
    'magic_cal_to_dl1',
]


class EventInfoContainer(Container):
    """
    Container to store the following event information:
    - observation/event/telescope IDs
    - telescope pointing direction
    - event timing information
    - parameters of a cleaned image
    """

    obs_id = Field(-1, 'Observation ID')
    event_id = Field(-1, 'Event ID')
    tel_id = Field(-1, 'Telescope ID')
    alt_tel = Field(-1, 'Telescope pointing altitude', u.rad)
    az_tel = Field(-1, 'Telescope pointing azimuth', u.rad)
    time_sec = Field(-1, 'Event time second')
    time_nanosec = Field(-1, 'Event time nanosecond')
    n_pixels = Field(-1, 'Number of pixels of a cleaned image')
    n_islands = Field(-1, 'Number of islands of a cleaned image')


def magic_cal_to_dl1(input_file, output_dir, config, process_run=False):
    """
    Processes MAGIC calibrated data to DL1.

    Parameters
    ----------
    input_file: str
        Path to an input MAGIC calibrated data file
    output_dir: str
        Path to a directory where to save an output DL1 data file
    config: dict
        Configuration for the LST-1 + MAGIC analysis
    process_run: bool
        If true, it processes all the sub-run files belonging to the
        same observation ID of an input sub-run file (default: false)
    """

    event_source = MAGICEventSource(input_file, process_run=process_run)

    obs_id = event_source.obs_ids[0]
    tel_id = event_source.telescope

    logger.info(f'\nProcess the following data (process_run = {process_run}):')
    for root_file in event_source.file_list:
        logger.info(root_file)

    # Configure the MAGIC cleaning:
    config_cleaning = config['MAGIC']['magic_clean']

    if config_cleaning['find_hotpixels'] == 'auto':
        config_cleaning.update({'find_hotpixels': True})

    logger.info('\nConfiguration for the image cleaning:')
    logger.info(config_cleaning)

    ped_type = config_cleaning.pop('pedestal_type')
    i_ped_type = np.where(np.array(pedestal_types) == ped_type)[0][0]

    camera_geom = event_source.subarray.tel[tel_id].camera.geometry
    magic_clean = MAGICClean(camera_geom, config_cleaning)

    # Prepare for saving data to an output file:
    Path(output_dir).mkdir(exist_ok=True, parents=True)

    if process_run:
        output_file = f'{output_dir}/dl1_M{tel_id}.Run{obs_id:08}.h5'
    else:
        subrun_id = event_source.metadata['subrun_number'][0]
        output_file = f'{output_dir}/dl1_M{tel_id}.Run{obs_id:08}.{subrun_id:03}.h5'

    # Process the events:
    logger.info('\nProcessing the events:')
    n_events_skipped = 0

    with HDF5TableWriter(output_file, 'events', mode='w') as writer:

        for event in event_source:

            if event.count % 100 == 0:
                logger.info(f'{event.count} events')

            # Apply the image cleaning:
            dead_pixels = event.mon.tel[tel_id].pixel_status.hardware_failing_pixels[0]
            badrms_pixels = event.mon.tel[tel_id].pixel_status.pedestal_failing_pixels[i_ped_type]
            unsuitable_mask = np.logical_or(dead_pixels, badrms_pixels)

            signal_pixels, image, peak_time = magic_clean.clean_image(
                event.dl1.tel[tel_id].image, event.dl1.tel[tel_id].peak_time, unsuitable_mask,
            )

            image_cleaned = image.copy()
            image_cleaned[~signal_pixels] = 0

            peak_time_cleaned = peak_time.copy()
            peak_time_cleaned[~signal_pixels] = 0

            n_pixels = np.count_nonzero(signal_pixels)
            n_islands, _ = number_of_islands(camera_geom, signal_pixels)

            if n_pixels == 0:
                logger.warning(f'--> {event.count} event (event ID: {event.index.event_id}): ' \
                               'Could not survive the image cleaning. Skipping.')
                n_events_skipped += 1
                continue

            # Try to compute the Hillas parameters:
            try:
                hillas_params = hillas_parameters(camera_geom, image_cleaned)
            except:
                logger.warning(f'--> {event.count} event (event ID: {event.index.event_id}): ' \
                               'Hillas parameters computation failed. Skipping.')
                n_events_skipped += 1
                continue

            # Try to compute the timing parameters:
            try:
                timing_params = timing_parameters(
                    camera_geom, image_cleaned, peak_time_cleaned, hillas_params, signal_pixels,
                )
            except:
                logger.warning(f'--> {event.count} event (event ID: {event.index.event_id}): ' \
                               'Timing parameters computation failed. Skipping.')
                n_events_skipped += 1
                continue

            # Try to compute the leakage parameters:
            try:
                leakage_params = leakage_parameters(camera_geom, image_cleaned, signal_pixels)
            except:
                logger.warning(f'--> {event.count} event (event ID: {event.index.event_id}): ' \
                               'Leakage parameters computation failed. Skipping.')
                n_events_skipped += 1
                continue

            # Set the event information to the container.
            # To keep the precision of a timestamp, here we set the integral and
            # fractional parts separately as "time_sec" and "time_nanosec":
            timestamp = event.trigger.tel[tel_id].time.to_value(format='unix', subfmt='long')
            fractional, integral = np.modf(timestamp)

            time_sec = int(np.round(integral))
            time_nanosec = int(np.round(fractional * sec2nsec))

            event_info = EventInfoContainer(
                obs_id=event.index.obs_id,
                event_id=event.index.event_id,
                alt_tel=event.pointing.tel[tel_id].altitude,
                az_tel=event.pointing.tel[tel_id].azimuth,
                time_sec=time_sec,
                time_nanosec=time_nanosec,
                n_pixels=n_pixels,
                n_islands=n_islands,
            )

            # Reset the telescope IDs:
            if tel_id == 1:
                event_info.tel_id = 2   # MAGIC-I

            elif tel_id == 2:
                event_info.tel_id = 3   # MAGIC-II

            # Save the parameters to the output file:
            writer.write('params', (event_info, hillas_params, timing_params, leakage_params))

        n_events_processed = event.count + 1

        logger.info(f'\nIn total {n_events_processed} events are processed.')
        logger.info(f'({n_events_skipped} events are skipped)')

    # Reset the telescope IDs of the telescope descriptions:
    tel_descriptions = {
        2: event_source.subarray.tel[1],   # MAGIC-I
        3: event_source.subarray.tel[2],   # MAGIC-II
    }

    # Save the subarray description.
    # Here we save the MAGIC telescope positions relative to the center of the
    # LST-1 + MAGIC array, which are also used for sim_telarray simulations:
    subarray = SubarrayDescription('MAGIC', tel_positions, tel_descriptions)
    subarray.to_hdf(output_file)

    logger.info('\nOutput file:')
    logger.info(output_file)

    logger.info('\nDone.')


def main():

    start_time = time.time()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--input-file', '-i', dest='input_file', type=str, required=True,
        help='Path to an input MAGIC calibrated data file (*_Y_*.root).',
    )

    parser.add_argument(
        '--output-dir', '-o', dest='output_dir', type=str, default='./data',
        help='Path to a directory where to save an output DL1 data file.',
    )

    parser.add_argument(
        '--config-file', '-c', dest='config_file', type=str, default='./config.yaml',
        help='Path to a yaml configuration file.',
    )

    parser.add_argument(
        '--process-run', dest='process_run', action='store_true',
        help='Processes all the sub-run files of the same observation ID at once.',
    )

    args = parser.parse_args()

    with open(args.config_file, 'rb') as f:
        config = yaml.safe_load(f)

    magic_cal_to_dl1(args.input_file, args.output_dir, config, args.process_run)

    process_time = time.time() - start_time
    logger.info(f'\nProcess time: {process_time:.0f} [sec]\n')


if __name__ == '__main__':
    main()