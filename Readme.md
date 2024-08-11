# Find Trip

#### Quick start:

- You can run the script in terminal with the following syntax:
    
    `python findtrip --place Washigton --distance 20`
#### Description:

- This script finds random city from given point within distance

### Line arguments:

- `--place [-p]`
    
	- original point as center for searching nearby settlements
	- form should be address or part of address
	- example: New York, 'Times Square, New York', London
	- use quotation marks if you want to type addresses with multiple words
	- optional argument, default value is 'New York'

- `--distance [-d]` 
	- distance from the place of origin where algoritmus is searching
	- unit is kilometer
	- optional argument, default value is '20'

### Cached:
- can be found as script `findtrip_cached.py` 
- adds option to search in previously results
- can be run without internet connection or on devices, where Open Street Map module is hard to install (et. mobile phones, tablets...)
- previous result are saved in file `findtrip_history.dat` and need to transfered to be used in cached version
