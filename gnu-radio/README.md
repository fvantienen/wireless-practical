# GNU Radio energy detector
This is a basic energy detector for DVB-T channels using GNU-radio.

## How to use the detector
- Execute `./dvbt_detector.py` (For help execute `./dvbt_detector.py --help`).
- Run `./gen_graphs.py` to generate the graphs.

## Detector options
```
Usage: dvbt_detector.py [options]

Options:
  -h, --help            show this help message and exit
  -q                    Disables debugging information (quiet mode)
  --freq_min=FREQ_MIN   The minimum frequency to search from in MHz
  --freq_max=FREQ_MAX   The maximum frequency to search from in MHz
  --freq_step=FREQ_STEP
                        The frequency steps to take while searching in MHz
  --threshold=THRESHOLD
                        Threshold in dB used for the detector
  --wait_time=WAIT_TIME
                        Amount of time to wait between fequency steps in
                        seconds
  -o OUTPUT_FILE, --output_file=OUTPUT_FILE
                        The output file for the CSV data
```