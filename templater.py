#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Created by: Nicholas Murphy on 10/18/2017

import sys, os
import logging
import argparse
import re


# Logging parameters
logger = logging.getLogger(__name__)
hdlr = logging.FileHandler('templater.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO) # Change from info to debug to see detailed log messages


def main():
    # Get the template file:
    # Given the path of the file from a shell call parameter
    template_filepath, result_filepath, env_filepath = get_file_names()
    template_file_lines = read_file(template_filepath)

    # Parse the template file (Use jnja library for building a template?)
    template_str = ''
    env_list = []

    for line in template_file_lines:
        # Reset variables at start of loop
        placeholder_line_list = []
        env_name = ''
        env_value = ''

        # Only look at lines with placeholder values in it
        if '{{' in line and '}}' in line:
            # Find the placeholder(s) value(s):
            #  {{env.Placeholder_value}} or {{env.Placeholder_value}}...{{env.Placeholder_value}}...etc
            placeholder_line = findPlaceholder(line)

            # Characters to be replaced in the placeholder line
            replace_map = {'{{': ' ', '}}': ' '}

            # restructure the placeholder line for parsing
            placeholder_line_list = (multireplace(placeholder_line, replace_map)).strip().split(' ')

            # Debug print to see what placeholders were foud in the line
            logger.debug('placeholder_line: {}'.format(placeholder_line))

            # Put new str.format bracket placeholder's into the line
            line = line.replace(placeholder_line , '{}')
            template_str += line

            env_value = ''
            for placeholder in placeholder_line_list:
                # if the placeholder really is a placeholder
                if len(placeholder) > 1:
                    # Grab the actual env name from the placeholder
                    if 'env.' in placeholder:
                        # If the env var name is led by a 'env.'
                        env_name = placeholder.strip('{}')[4:].upper()
                        logger.debug("env_name: {}".format(env_name))

                    else:
                        # Actual env var name is alone inside the '{{...}}'
                        env_name = placeholder.strip('{}').upper()
                        logger.debug("env_name: {}".format(env_name))

                    try:
                        # Try to get the value of the env variable
                        env_value += os.environ[env_name]
                        logger.debug('sys_env: {}\n'.format(env_value))

                    # Keyerror means that the env_name wasn't set or the sys env variable isn't
                    # found so default should be used
                    except (KeyError, UnboundLocalError) as e:
                        # Check if the placeholder is a default .env file variable
                        env_file_lines = read_file(env_filepath)
                        # Grab out the .env default value from file
                        for env_line in env_file_lines:
                            if (env_name+'=') in env_line.strip() and '#' not in env_line.strip():
                                env_value += env_line[len(env_name)+1:].rstrip()
                                logger.debug('def_env: {}\n'.format(env_value))

                # If the 'placeholder' is actually not a placeholder and is a special
                # character or something
                else:
                    env_value += placeholder

            # Add the env value from either the sys env var or from the default from the /.env file
            env_list.append(env_value)

        # Add in the non-placeholder containing lines back unchanged to the template string
        else:
            template_str +=  line

    # Debug print statements to see the re-templated structure before the string format function
    # and the number of placeholders found matches how many are to be inserted
    logger.debug('Template before inserting env var\'s\n{}'.format(template_str))
    logger.debug('template placeholders:{}\nenv_vars:{}'.format(template_str.count('}'), len(env_list)))

    # Format insert the env values back into the template string
    template_str = template_str.format(*env_list)

    # Write the newly formatted/filled-out template to file
    write_file(result_filepath, template_str)


# Open and read words from the stored word_banks and returns a list of lines
def read_file(filename):
    logger.debug("Reading template from file:")
    with open(os.path.join(sys.path[0], filename), "r") as rfile:
        lines = rfile.readlines()
    return lines


def write_file(filename, str_to_write):
    logger.debug("Generating completed template:")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(os.path.join(sys.path[0], filename), "a+") as wfile:
        wfile.truncate(0) # Clear the file before writing to it
        wfile.write(str_to_write) # write the filledout template to file


def get_file_names():
    logger.debug("Getting cmd flag arguments:")
    # Set up arg parse command line settings
    parser = argparse.ArgumentParser(
        description='Fills out a template file with environment variables')
    parser.add_argument(
        '-f', '--filename_path',
        metavar='f',
        type=str,
        default='./template.yaml',
        help='The path and filename of the template file to be filled out')
    parser.add_argument(
        '-r', '--resulting_file_path',
        metavar='r',
        type=str,
        default='./result.yaml',
        help="The path and filename of the resulting filled-out template file to be created")
    parser.add_argument(
        '-e', '--env_file_path',
        metavar='e',
        type=str,
        default='./.env',
        help="The path and filename of the default env file to be used when a sys env var isn't set")

    args = parser.parse_args()

    return args.filename_path, args.resulting_file_path, args.env_file_path


def multireplace(string, replacements):
    """
    Given a string and a replacement map, it returns the replaced string.
    :param str string: string to execute replacements on
    :param dict replacements: replacement dictionary {value to find: value to replace}
    :rtype: str
    """
    logger.debug("Multireplacing a string:")
    # Place longer ones first to keep shorter substrings from matching where the longer ones should take place
    # For instance given the replacements {'ab': 'AB', 'abc': 'ABC'} against the string 'hey abc', it should produce
    # 'hey ABC' and not 'hey ABc'
    substrs = sorted(replacements, key=len, reverse=True)

    # Create a big OR regex that matches any of the substrings to replace
    regexp = re.compile('|'.join(map(re.escape, substrs)))

    # For each match, look up the new string in the replacements
    return regexp.sub(lambda match: replacements[match.group(0)], string)


def findPlaceholder(str):
    logger.debug("Finding placeholders in template line:")
    p = _reHelper()(str)
    return p.group()

def _reHelper():
    return re.compile(r'(\{\{.*\}\})', flags=re.IGNORECASE).search


# Only run this script from the command line
if __name__ == '__main__':
    logger.debug("Running main program:")
    main()
