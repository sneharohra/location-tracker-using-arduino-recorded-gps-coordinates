#
#  Who wrote this -- fix it yourself?
#  Date and Time?
#  Stuff at the header?
#  What course did you write this for?
#  What does this program do?
# 
import glob
import os

import sys  # Why are you importing this?  What reason do you need this?
import datetime  # Why do you need this?  How is it used?
import pandas as pd  # What is this used for?

import writing_out_placemark_example_FOR_PUBLICATIONs


def glob_data(path):
    abs_path = os.path.abspath(path)
    file_list = glob.glob(abs_path + "/**/*.txt")
    with open('global_file.txt', 'w') as p:
        for single_file in file_list:
            with open(single_file, 'r') as f:
                lines = f.readlines()
            p.writelines(lines)


# Why use this?
# How does PANDAS help us?

# Print usage if we don't have enough args.
def usage():
    if len(sys.argv) < 3:
        print('Usage: python3 GPS_to_KML.py GPS_Filename.txt KML_Filename.kml')
        exit()

    # Get the filename args.
    gps_filename = sys.argv[1]
    kml_filename = sys.argv[2]


# Open the gps data file to read.

# Create an empty dictionary for the gps data.
gps_info = {}


# A function to read the file and fill a dictionary with datapoint information:
#
# This should be given a file name and return a data structure.
# One might want to use pynema instead.
#
def get_gps_data():
    # For every line in the gps data file.
    with open("global_file.txt", 'r') as f:
        gps_file = f.readlines()
    for line in gps_file:
        # If this line is an RMC line.
        if line.split(',')[0] == "$GPRMC":
            # Split the line on commas and set each value to a variable (based on its location per the protocol).
            try:
                label, timestamp, validity, latitude, lat_dir, longitude, long_dir, knots, course, \
                datestamp, variation, var_dir, checksum = line.split(',')
            # If this line is missing a value or has too many, assume it's an error and skip the line.
            except ValueError:
                continue

            # If the validity is 'V' (per the protocol, a gps error), skip the line.
            if validity == 'V':
                continue

            # Get the timestamp into a datetime object.
            # Start by getting the HHMMSS part, the part before the '.'.
            timestamp_split = timestamp.split('.')[0]
            # Join every two characters with ':' (that is, get it into HH:MM:SS form), and then append the MS part.
            time_str = ':'.join([timestamp_split[index:index + 2] for index in range(0, len(timestamp_split), 2)]) + \
                       ':' + timestamp.split('.')[1]
            # Use strptime to convert the string we just put together into a datetime object.
            date_time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S:%f')

            # Convert the latitude into degrees.
            # This math might be wrong.
            degrees = int(float(latitude) / 100)
            mins = float(latitude) - (degrees * 100)
            # N is positive, S is negative.
            if lat_dir == 'N':
                fixed_latitude = degrees + (mins / 60)
            else:
                fixed_latitude = -degrees + (-mins / 60)

            # Convert the longitude into degrees.
            degrees = int(float(longitude) / 100)
            mins = float(longitude) - (degrees * 100)
            # E is positive, W is negative.
            if long_dir == 'E':
                fixed_longitude = degrees + (mins / 60)
            else:
                fixed_longitude = -degrees + (-mins / 60)

            # Add this line's information to the dictionary, with the timestamp as the key.
            # Using the timestamp means that multiple lines from the same time (e.g. if there's also GGA from this time)
            # will be combined.
            # If it's already in the dictionary, we want to update the entry instead of setting to keep from overriding
            #    any GGA information from that time (such as altitude).
            if timestamp in gps_info:
                gps_info[timestamp].update({'datetime': date_time_obj, 'latitude': round(fixed_latitude, 6),
                                            'longitude': round(fixed_longitude, 6), 'knots': float(knots),
                                            'course': course, 'variation': variation})
            else:
                gps_info[timestamp] = {'datetime': date_time_obj, 'latitude': round(fixed_latitude, 6),
                                       'longitude': round(fixed_longitude, 6),
                                       'knots': knots, 'course': course, 'variation': variation}

        # If this line is a GGA line.
        elif line.split(',')[0] == "$GPGGA":
            # If the GPS quality indicator is not zero, this line should be valid.
            if line.split(',')[6] != '0':
                # Split the line on commas and set each value to a variable (based on its location per the protocol).
                try:
                    label, timestamp, latitude, lat_dir, longitude, long_dir, gps_quality, num_satellites, horiz_dilution, \
                    antenna_alt, antenna_alt_units, geoidal, geo_units, age_since_update, checksum = line.split(',')
                # If this failed, that means something is wrong with this line.
                except ValueError:
                    continue

                # Convert the latitude into degrees.
                degrees = int(float(latitude) / 100)
                mins = float(latitude) - (degrees * 100)
                # N is positive, S is negative.
                if lat_dir == 'N':
                    fixed_latitude = degrees + (mins / 60)
                else:
                    fixed_latitude = -degrees + (-mins / 60)

                # Convert the longitude into degrees.
                degrees = int(float(longitude) / 100)
                mins = float(longitude) - (degrees * 100)
                # E is positive, W is negative.
                if long_dir == 'E':
                    fixed_longitude = degrees + (mins / 60)
                else:
                    fixed_longitude = -degrees + (-mins / 60)

                # Add this line's information to the dictionary, with the timestamp as the key.
                # Using the timestamp means that multiple lines from the same time
                # (e.g. if there's also RMC from this time) will be combined.
                # If it's already in the dictionary, we want to update the entry instead of setting to keep
                #   from overriding any RMC information from that time (such as course).
                if timestamp in gps_info:
                    gps_info[timestamp].update({'latitude': round(fixed_latitude, 6),
                                                'longitude': round(fixed_longitude, 6),
                                                'altitude': float(antenna_alt)})
                else:
                    gps_info[timestamp] = {'latitude': round(fixed_latitude, 6), 'longitude': round(fixed_longitude, 6),
                                           'altitude': float(antenna_alt)}
        # We don't care about any other protocols.
        else:
            continue


def define_stops():
    # Get a list of all of the keys for the dictionary of GPS info.
    key_list = list(gps_info.keys())

    stops = {}
    # Iterate through the list of keys.
    key_index = 0
    while key_index < len(key_list) - 1:
        # Get the coordinates of the current and next entries in the dictionary.
        this_latitude = gps_info[key_list[key_index]]['latitude']
        this_longitude = gps_info[key_list[key_index]]['longitude']

        # next_timestamp = key_list[key_index]
        j = key_index
        flag = 0
        while j < len(key_list):
            if round(gps_info[key_list[j]]['latitude'], 5) == round(gps_info[key_list[j + 1]]['latitude'], 5) and \
                    round(gps_info[key_list[j]]['longitude'], 5) == round(gps_info[key_list[j + 1]]['longitude'], 5):
                flag = 1
                j += 1
            else:
                break
        next_latitude = gps_info[key_list[j]]['latitude']
        next_longitude = gps_info[key_list[j]]['longitude']

        key = str(round(this_latitude, 4)) + str(round(this_longitude, 4))
        if flag == 1:
            if 'datetime' in gps_info[key_list[key_index]].keys() and \
                    'datetime' in gps_info[key_list[j]].keys():
                this_timestamp = gps_info[key_list[key_index]]['datetime']
                next_timestamp = gps_info[key_list[j]]['datetime']
                time_diff = next_timestamp - this_timestamp
                parking_time = abs(time_diff.seconds)
                if key in stops.keys():
                    if parking_time > stops[key]['Parking_Time']:
                        stops[key]['Parking_Time'] = parking_time
                else:
                    stops[key] = gps_info[key_list[key_index]]
                    stops[key]['Parking_Time'] = parking_time
                key_index = j + 1
                continue
        key_index = j + 1

    return stops


#
# A function to remove redundant entries from the dictionary (to lower the number of points while preserving the line).
#
# For example, if the car is traveling in a straight line, then
# delete the middle point.
# Or, maybe don't.
# Perhaps there is a bitter method.
def remove_redundant_GPS_points():
    # Get a list of all of the keys for the dictionary of GPS info.
    key_list = list(gps_info.keys())


    # Iterate through the list of keys.
    for key_index in range(0, len(key_list) - 1):
        # Get the coordinates of the current and next entries in the dictionary.
        this_latitude = gps_info[key_list[key_index]]['latitude']
        next_latitude = gps_info[key_list[key_index + 1]]['latitude']
        this_longitude = gps_info[key_list[key_index]]['longitude']
        next_longitude = gps_info[key_list[key_index + 1]]['longitude']

        # If the coordinates are the same (rounded down a bit, to account for GPS skew)
        # meaning we haven't moved, remove one of the values.
        if round(this_latitude, 5) == round(next_latitude, 5) and round(this_longitude, 5) == round(next_longitude, 5):

            gps_info.pop(key_list[key_index])

            continue

        # If we didn't remove the data for the key right before this one, and this isn't the first key.
        if key_index != 0 and key_list[key_index - 1] in gps_info:

            # Get coordinates of the preceding entry.
            last_latitude = gps_info[key_list[key_index - 1]]['latitude']
            last_longitude = gps_info[key_list[key_index - 1]]['longitude']

            # Get the latitude and longitude differences in both directions.
            lat_diff_from_last = abs(this_latitude - last_latitude)
            long_diff_from_last = abs(this_longitude - last_longitude)
            lat_diff_from_next = abs(this_latitude - next_latitude)
            long_diff_from_next = abs(this_longitude - next_longitude)

            # If our speed is constant and we're moving in a straight line, remove the unnecessary point in between.
            tolerance = 0.01  # This is WAY TOO BIG!!
            if abs(lat_diff_from_last - lat_diff_from_next) <= tolerance and \
                    abs(long_diff_from_last - long_diff_from_next) <= tolerance:
                gps_info.pop(key_list[key_index])
                continue

            # If the last entry has speed data (some lines may not if they were only GGA).
            if 'knots' in gps_info[key_list[key_index - 1]]:

                # Get the speed of the last entry.
                last_speed = float(gps_info[key_list[key_index - 1]]['knots'])

                # Remove the entry if the difference in latitude or longitude is too high compared to the speed.
                # This manages errors where a GPS reading is way off (e.g. in the middle of the ocean.)
                if long_diff_from_last / 10 > last_speed or lat_diff_from_next / 10 > last_speed:
                    gps_info.pop(key_list[key_index])
                    continue

    # return stops


#
# Write the kml file.
#
# REWRITE THIS TO TAKE IN A FILENAME.
#
# Write now it outputs a path.
# Instead we want to output a flag for where the car spent a lot of time.
#
def write_out_KML_file():
    # Open it to write (such that it will be created if it does not already exist).
    kml_file = open('kml_filename.kml', 'w+')
    # Write the heading and style information.
    kml_file.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
    kml_file.write("<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n")
    kml_file.write("<Document>\n")
    kml_file.write("<Style id=\"cyanPoly\">\n"
                   "\t<LineStyle>\n"
                   "\t\t<color>ffffff00</color>\n"
                   "\t\t<width>6</width>\n"
                   "\t</LineStyle>\n"
                   "\t<PolyStyle>\n"
                   "\t\t<color>ffffff00</color>\n"
                   "\t</PolyStyle>\n"
                   "</Style>\n"
                   "<Placemark><styleUrl>#cyanPoly</styleUrl>\n"
                   "<LineString>\n"
                   "<Description>Speed in Knots, instead of altitude.</Description>\n"
                   "\t<extrude>1</extrude>\n"
                   "\t<tesselate>1</tesselate>\n"
                   "\t<altitudeMode>absolute</altitudeMode>\n"
                   "<coordinates>\n")

    # Every line is guaranteed to have a latitude and longitude.
    # If one does not have an altitude, it will just use the last altitude we had.
    last_alt = 0
    # Iterate through all of the entries we didn't prune.
    for line in gps_info.values():
        if 'altitude' in line:
            last_alt = line['altitude']
        # Write the coordinates to the file.
        kml_file.write('\t' + str(line['longitude']) + ',' + str(line['latitude']) + ',' + str(last_alt) + '\n')

    # Closing up the file.
    kml_file.write("        </coordinates>\n")
    kml_file.write("      </LineString>\n")
    kml_file.write("    </Placemark>\n")
    kml_file.write("  </Document>\n")
    kml_file.write("</kml>\n")


#
#  Here is the main routine:
# 
def main():
    # Call the functions to run the program overall.
    # if len(sys.argv) < 3:
    #     usage()
    #     quit()
    glob_data("all_data_files")
    get_gps_data()
    print('Instead of removing redundant GPS points. Itentify where the car is spending most of its time.')
    remove_redundant_GPS_points()

    stops_dict = define_stops()
    print('Instead of emitting a KML file with a path, emit a KML file with LOCATIONS on it.')
    # write_out_KML_file()
    writing_out_placemark_example_FOR_PUBLICATIONs.write_stop_file(stops_dict)


if __name__ == "__main__":
    main()
else:
    print("this is NOT main")
