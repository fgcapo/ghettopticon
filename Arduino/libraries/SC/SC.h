/**
 * SerialCommand - A Wiring/Arduino library to tokenize and parse commands
 * received over a serial port.
 * 
 * Copyright (C) 2012 Stefan Rado
 * Copyright (C) 2011 Steven Cogswell <steven.cogswell@gmail.com>
 *                    http://husks.wordpress.com
 * 
 * Version 20120522
 * 
 * This library is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this library.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef SerialCommand_h
#define SerialCommand_h

#if defined(WIRING) && WIRING >= 100
  #include <Wiring.h>
#elif defined(ARDUINO) && ARDUINO >= 100
  #include <Arduino.h>
#else
  #include <WProgram.h>
#endif
#include <string.h>

// Uncomment the next line to run the library in debug mode (verbose messages)
//#define SERIALCOMMAND_DEBUG


// array of name-command pairs must end with {NULL, NULL}

// Size of the input buffer in bytes (maximum length of one command plus arguments)
//template<int COMMAND_BUFFER_LENGTH=255>
#define COMMAND_BUFFER_LENGTH 255
class SerialCommand {
  public:
    // data structure to hold Command/Handler function key-value pairs
    struct Entry {
      const char *command;
      void (*function)();
    }; 

    typedef void (*DefaultHandler)(const char *);


    SerialCommand(const Entry *commandList,
                  DefaultHandler defaultHandler,
                  char terminator = '\n',
                  const char *delimiters = " ");

    void setDefaultHandler(DefaultHandler function);   // A handler to call when no valid command received.

    void readSerial();    // Main entry point.
    void clearBuffer();   // Clears the input buffer.
    char *next();         // Returns pointer to next token found in command buffer (for getting arguments to commands).


  private:
    
    // Command/handler array of {name, function} pairs
    // Array must end with {NULL, NULL}                             
    const Entry *commandList;

    void (*defaultHandler)(const char *);    // pointer to the default handler function

    const char *delim; // null-terminated list of delimiter characters for tokenizing (default " ")
    char term;         // character that signals end of command (default '\n')

    char buffer[COMMAND_BUFFER_LENGTH + 1]; // Buffer of stored characters while waiting for terminator character
    byte bufPos;                        // Current position in the buffer
    char *last;                         // State variable used by strtok_r during processing
};

#endif //SerialCommand_h
