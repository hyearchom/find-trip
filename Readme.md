# Find Trip

#### Quick start:

`git clone https://github.com/hyearchom/find-trip`
`pip install osmnx`
`python findtrip --place 'Washigton' --distance 20`

- Use terminal with python and wheel to run the script
    
#### Description:

- This script finds random city from given point within distance
- Can be run without internet connection or on devices, where Open Street Map module is hard to install (et. mobile phones, tablets...)
- Previous result are saved in file `.dat` files and need to transfered to be used in cached version

### Line arguments:

- `--place [-p]`
	- original point as center for searching nearby settlements
	- form should be address or part of address
	- example: 'New York', 'Times Square, New York', London
	- use quotation marks if you want to type addresses with multiple words
	- optional argument after setting default value (via`--home` argument)

- `--distance [-d]` 
	- distance from the place of origin where algoritmus is searching
	- unit is kilometer
	- optional argument, default value is '20'
	
- `--home`
	- saves default value for `--place` argument and ends script

- `--no_history [-n]`
	- prevent script from saving anything into data folder after search
	- this does not effect OSMX module, which creates cache folder by default if you try to search from a new place