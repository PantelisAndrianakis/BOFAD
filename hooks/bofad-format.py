import os

def is_control_structure(line):
    """Check if line starts with a control structure keyword."""
    stripped = line.strip()
    return (stripped.startswith('catch (') or 
            stripped.startswith('else') or 
            stripped.startswith('break') or 
            stripped.startswith('case ') or 
            stripped.startswith('default:') or 
            stripped.startswith('finally') or 
            stripped.startswith('try {') or
            stripped.startswith('},') or
            stripped.startswith('* ') or
            stripped.startswith('while (') or  # Add while for do-while loops
            stripped == 'else')  # Add exact match for standalone else

def is_comment(line):
    """Check if line is a comment."""
    stripped = line.strip()
    return stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*')

def is_formatter_comment(line):
    """Check if line is a formatter comment that should not have empty lines before it."""
    stripped = line.strip()
    return stripped.startswith('// @formatter:') or stripped.startswith('//@formatter:')

def is_modifier_comment(line):
    """Check if line is a comment that starts with Java modifiers or special keywords."""
    stripped = line.strip()
    return (stripped.startswith('// public ') or
            stripped.startswith('// protected ') or
            stripped.startswith('// private ') or
            stripped.startswith('// final ') or
            stripped.startswith('// static ') or
            stripped.startswith('// Fallthrough') or
            stripped.startswith('// fallthrough') or
            stripped.startswith('// LOGGER.') or
            stripped.startswith('// PacketLogger.') or
            stripped.startswith('// zone.') or
            stripped.startswith('// System.out.') or
            stripped.startswith('// _') or
            stripped.startswith('// else') or 
            stripped.startswith('}));') or
            stripped.startswith('}).start()') or
            stripped.startswith('}.load()') or
            stripped.startswith('}).forEach'))

def is_meaningful_code_line(line):
    """Check if line contains meaningful code (not just braces or empty)."""
    stripped = line.strip()
    return (stripped and 
            not stripped in {'{', '}', "});", "};", "}.execute();"} and
            not is_comment(line) and
            not is_control_structure(line))

def is_array_definition_start(line):
    """Check if line starts an array or collection definition."""
    stripped = line.strip()
    # Check for array declarations ending with = followed by {
    return ('=' in stripped and stripped.endswith('{') and
            ('[]' in stripped or 'List<' in stripped or 'Set<' in stripped or 
             'Map<' in stripped or 'Collection<' in stripped or 'ArrayList<' in stripped or
             'HashSet<' in stripped or 'HashMap<' in stripped))

def is_inside_array_context(lines, current_index):
    """Check if we're currently inside an array/collection definition context."""
    # Look backwards to find if we're inside an array definition
    brace_count = 0
    for i in range(current_index, -1, -1):
        line = lines[i].strip()
        
        # Count closing braces
        brace_count += line.count('}')
        # Count opening braces
        brace_count -= line.count('{')
        
        # If we have more closing than opening braces, we're not in an array
        if brace_count > 0:
            return False
            
        # If we find an array definition start and braces are balanced or we have opening braces
        if brace_count <= 0 and is_array_definition_start(line):
            return True
            
        # If we hit a method/class/control structure start, stop looking
        if (line.endswith('{') and not is_array_definition_start(line) and
            ('(' in line or 'class ' in line or 'interface ' in line or 
             'if ' in line or 'for ' in line or 'while ' in line or 'try' in line)):
            break
    
    return False

def process_java_file(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8', newline='') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(input_path, 'r', encoding='latin-1', newline='') as f:
            content = f.read()
    
    lines = content.splitlines()
    processed_lines = []
    in_javadoc = False
    in_static_block = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Normalize whitespace-only lines to truly empty (no trailing tabs/spaces)
        if stripped == '':
            line = ''

        # Check if current line is empty and should be removed
        # Pattern: previous line ends with "();" -> current empty line -> next line starts with "static"
        if (stripped == '' and  # Current line is empty
            i > 0 and i + 1 < len(lines) and
            lines[i - 1].strip().endswith('();') and  # Previous line ends with "();"
            lines[i + 1].strip().startswith('static')):  # Next line starts with "static"
            
            # Skip this empty line
            i += 1
            continue
        
        # NEW: Handle }); -> return pattern - add empty line before return
        if (i > 0 and
            not in_javadoc and not in_static_block and
            stripped.startswith('return') and  # Current line starts with return
            lines[i-1].strip().endswith('});')):  # Previous line ends with });
            
            # Get indentation from current line
            tab_count = len(line) - len(line.lstrip('\t'))
            
            # Add empty line before return
            processed_lines.append('')
        
        # FIXED: Check for Javadoc start/end - handle single-line Javadoc comments
        if stripped.startswith('/**'):
            if stripped.endswith('*/'):
                # Single-line Javadoc comment, don't change in_javadoc state
                pass
            else:
                # Multi-line Javadoc comment starts
                in_javadoc = True
        elif in_javadoc and stripped.endswith('*/'):
            in_javadoc = False
            
        # Check for static block start/end
        if stripped == 'static' and i+1 < len(lines) and lines[i+1].strip() == '{':
            in_static_block = True
            processed_lines.append(line)
            i += 1
            processed_lines.append(lines[i])
            i += 1
            continue
            
        if in_static_block and stripped == '}':
            in_static_block = False
            processed_lines.append(line)
            i += 1
            continue
            
        # NEW: Handle NpcStringId pattern (add empty line after line ending with comma)
        if (i+1 < len(lines) and
            not in_javadoc and not in_static_block and
            stripped.endswith(',') and  # Current line ends with comma
            lines[i].strip().startswith('NpcStringId.') and  # Current line starts with NpcStringId.
            lines[i+1].strip().startswith('// NpcStringId.')):  # Next line is // NpcStringId. comment
            
            # Check if there's a line after the comment that also starts with NpcStringId.
            if (i+2 < len(lines) and 
                lines[i+2].strip().startswith('NpcStringId.')):
                # Don't add empty line for this NpcStringId pattern
                processed_lines.append(line)
                i += 1
                continue
        if (i+1 < len(lines) and i+2 < len(lines) and
            not in_javadoc and not in_static_block and
            stripped.endswith('};') and  # Current line ends with };
            lines[i+1].strip().startswith('//') and  # Next line is comment
            not is_formatter_comment(lines[i+1]) and  # Next line is not @formatter comment
            not is_modifier_comment(lines[i+1]) and  # Next line is not modifier comment
            lines[i+2].strip() and  # Line after comment has content
            not is_comment(lines[i+2])):  # Line after comment is not a comment
            
            # Check if all three lines have the same indentation level
            curr_tab_count = len(line) - len(line.lstrip('\t'))
            next_tab_count = len(lines[i+1]) - len(lines[i+1].lstrip('\t'))
            after_tab_count = len(lines[i+2]) - len(lines[i+2].lstrip('\t'))
            
            if curr_tab_count == next_tab_count == after_tab_count:
                # Add the current line (};)
                processed_lines.append(line)
                
                # Add empty line with proper indentation
                processed_lines.append('')
                
                # Skip to next iteration
                i += 1
                continue
            
        # Handle case where } is followed by // comment and then non-comment, non-{, non-else
        if (i+2 < len(lines) and 
            not in_javadoc and not in_static_block and
            stripped == '}' and 
            lines[i+1].strip().startswith('//') and  # Next line is comment
            not is_formatter_comment(lines[i+1]) and  # Next line is not @formatter comment
            not is_modifier_comment(lines[i+1]) and  # Next line is not modifier/fallthrough comment
            not is_comment(lines[i+2]) and  # Line after comment is not a comment
            not lines[i+2].strip().startswith('{') and  # Line after comment doesn't start with {
            not lines[i+2].strip().startswith('else') and  # Line after comment doesn't start with else
            not lines[i+2].strip().startswith('case ') and  # Line after comment doesn't start with case
            not lines[i+2].strip() == 'else'):  # NEW: Line after comment is not standalone else
            
            # Check if there's already an empty line before the comment
            if i > 0 and lines[i-1].strip() != '':
                # Add the current line (})
                processed_lines.append(line)
                
                # Get indentation from the comment line
                tab_count = len(lines[i+1]) - len(lines[i+1].lstrip('\t'))
                
                # Add empty line before comment only if one doesn't exist
                processed_lines.append('')
                
            # Skip to the comment line in next iteration
            i += 1
            continue
            
        # NEW: Check for @formatter:on -> comment -> non-comment pattern (PRIORITY CHECK)
        if (i > 0 and i+1 < len(lines) and
            not in_javadoc and not in_static_block and
            stripped.startswith('//') and  # Current line is single-line comment
            not is_formatter_comment(line) and  # Current line is not @formatter comment
            not is_modifier_comment(line) and  # Current line is not modifier comment
            (lines[i-1].strip() == '// @formatter:on' or lines[i-1].strip() == '//@formatter:on') and  # Previous line is @formatter:on (both formats)
            not is_comment(lines[i+1]) and  # Next line is not a comment
            lines[i+1].strip() and  # Next line has content
            not (lines[i+1].strip() == 'else' or lines[i+1].strip().startswith('else if'))):    # Next line is not 'else' or 'else if'
            
            # Check if all three lines have the same indentation level
            prev_tab_count = len(lines[i-1]) - len(lines[i-1].lstrip('\t'))
            curr_tab_count = len(line) - len(line.lstrip('\t'))
            next_tab_count = len(lines[i+1]) - len(lines[i+1].lstrip('\t'))
            
            if prev_tab_count == curr_tab_count == next_tab_count:
                # Check if we already added an empty line
                last_added_line = processed_lines[-1] if processed_lines else ""
                last_added_is_empty = last_added_line.strip() == ""
                
                # Only add empty line if we haven't already added one
                if not last_added_is_empty:
                    # Add empty line before the comment
                    processed_lines.append('')
            
        # Enhanced pattern matching for comments between code lines
        # Check for pattern: meaningful code -> comment -> (anything except empty or })
        elif (i > 0 and i+1 < len(lines) and
            not in_javadoc and not in_static_block and
            stripped.startswith('//') and  # Current line is single-line comment
            not is_formatter_comment(line) and  # Current line is not @formatter comment
            not is_modifier_comment(line)):  # Current line is not modifier comment
            
            # Check if previous line is meaningful code OR a closing brace (not just a brace or empty)
            prev_line_stripped = lines[i-1].strip()
            prev_line_meaningful = (is_meaningful_code_line(lines[i-1]) or 
                                   prev_line_stripped in {'}', '};', '}.execute();'} or
                                   prev_line_stripped.startswith('/**'))  # FIXED: Also consider single-line Javadoc as meaningful
            
            # Check if next line is not empty and not just a closing brace
            next_line = lines[i+1].strip()
            next_line_acceptable = next_line and next_line != '}'
            
            # Check if all lines have the same indentation level
            prev_tab_count = len(lines[i-1]) - len(lines[i-1].lstrip('\t'))
            curr_tab_count = len(line) - len(line.lstrip('\t'))
            next_tab_count = len(lines[i+1]) - len(lines[i+1].lstrip('\t'))
            
            # NEW: Check for NpcStringId pattern exception
            is_npcstringid_pattern = (
                lines[i-1].strip().startswith('NpcStringId.') and  # Previous line starts with NpcStringId.
                stripped.startswith('// NpcStringId.') and  # Current line is // NpcStringId. comment
                lines[i+1].strip().startswith('NpcStringId.')  # Next line starts with NpcStringId.
            )
            
            # NEW: Check if comment is a commented-out version of similar code
            is_commented_code_pattern = False
            if stripped.startswith('// ') and len(stripped) > 3:
                comment_content = stripped[3:].strip()  # Get content after "// "
                # Extract first word/method call from both lines for comparison
                prev_words = prev_line_stripped.split('.')
                comment_words = comment_content.split('.')
                
                # Check if they start with the same object/method pattern
                if (len(prev_words) >= 2 and len(comment_words) >= 2 and
                    prev_words[0] == comment_words[0]):  # Same object name
                    is_commented_code_pattern = True
            
            # NEW: Check if comment is "// else"
            is_commented_else = stripped == '// else'
            
            # NEW: Check for } -> // -> case or } -> // -> else pattern
            is_brace_comment_case_pattern = (
                prev_line_stripped == '}' and  # Previous line is closing brace
                stripped.startswith('//') and  # Current line is comment
                (lines[i+1].strip().startswith('case ') or  # Next line starts with case
                 lines[i+1].strip() == 'else' or  # Next line is standalone else
                 lines[i+1].strip().startswith('else '))  # Next line starts with else
            )
            
            # NEW: Check for array-like patterns where we shouldn't add empty lines
            is_array_like_pattern = False
            if i > 0 and i+1 < len(lines):
                # Check if we're in a simple array-like structure
                # Pattern: previous line has comma + (number or ID), current line is comment, next line has number/ID or closing
                prev_has_comma_and_value = (
                    prev_line_stripped.endswith(',') or  # Line ends with comma
                    (',' in prev_line_stripped and '//' in prev_line_stripped)  # Line has comma and inline comment
                ) and (
                    any(char.isdigit() for char in prev_line_stripped) or  # Contains numbers
                    'NpcStringId.' in prev_line_stripped or
                    'SystemMessageId.' in prev_line_stripped
                )
                
                next_is_value_or_end = (
                    any(char.isdigit() for char in lines[i+1].strip()) or  # Next line contains numbers
                    lines[i+1].strip().startswith('NpcStringId.') or
                    lines[i+1].strip().startswith('SystemMessageId.') or
                    lines[i+1].strip() == '};' or  # Array closing
                    lines[i+1].strip() == '}'  # Block closing
                )
                
                is_array_like_pattern = prev_has_comma_and_value and next_is_value_or_end
            
            if (prev_line_meaningful and next_line_acceptable and 
                prev_tab_count == curr_tab_count == next_tab_count and
                not is_npcstringid_pattern and  # Don't add empty line for NpcStringId pattern
                not is_commented_code_pattern and  # Don't add empty line for commented-out similar code
                not is_commented_else and  # Don't add empty line for "// else"
                not is_brace_comment_case_pattern and  # NEW: Don't add empty line for } -> // -> case pattern
                not is_array_like_pattern):  # NEW: Don't add empty line for simple array-like patterns
                
                # Check if we already added an empty line
                last_added_line = processed_lines[-1] if processed_lines else ""
                last_added_is_empty = last_added_line.strip() == ""
                
                # Only add empty line if we haven't already added one
                if not last_added_is_empty:
                    # Add empty line before the comment
                    processed_lines.append('')
        
        # Check for pattern: @formatter comment -> comment -> non-comment (all with same indentation)
        elif (i > 0 and i+1 < len(lines) and
            not in_javadoc and not in_static_block and
            stripped.startswith('//') and  # Current line is single-line comment
            not is_formatter_comment(line) and  # Current line is not @formatter comment
            not is_modifier_comment(line) and  # Current line is not modifier comment
            is_formatter_comment(lines[i-1]) and  # Previous line is @formatter comment
            not is_comment(lines[i+1]) and  # Next line is not a comment
            lines[i+1].strip() and  # Next line has content
            not (lines[i+1].strip() == 'else' or lines[i+1].strip().startswith('else if'))):    # Next line is not 'else' or 'else if'
            
            # Check if all three lines have the same indentation level
            prev_tab_count = len(lines[i-1]) - len(lines[i-1].lstrip('\t'))
            curr_tab_count = len(line) - len(line.lstrip('\t'))
            next_tab_count = len(lines[i+1]) - len(lines[i+1].lstrip('\t'))
            
            if prev_tab_count == curr_tab_count == next_tab_count:
                # Check if we already added an empty line
                last_added_line = processed_lines[-1] if processed_lines else ""
                last_added_is_empty = last_added_line.strip() == ""
                
                # Only add empty line if we haven't already added one
                if not last_added_is_empty:
                    # Add empty line before the comment
                    processed_lines.append('')
        
        # Existing: Check if current line is a single-line comment followed by if
        elif (i > 0 and i+1 < len(lines) and
            not in_javadoc and not in_static_block and
            stripped.startswith('//') and  # Current line is single-line comment
            not is_formatter_comment(line) and  # Current line is not @formatter comment
            not is_modifier_comment(line) and  # Current line is not modifier comment
            not is_comment(lines[i-1]) and  # Previous line is not a comment
            lines[i+1].strip().startswith('if ') and  # Next line starts with if
            not lines[i-1].strip().endswith('{') and  # Not after opening brace
            lines[i-1].strip() != 'else' and    # Previous line is not 'else'
            not lines[i-1].strip().startswith('else if')):    # Previous line is not 'else if'
            
            # Check if we already added an empty line (check the last line in processed_lines)
            last_added_line = processed_lines[-1] if processed_lines else ""
            last_added_is_empty = last_added_line.strip() == ""
            
            # Only add empty line if we haven't already added one
            if not last_added_is_empty:
                # Add empty line before the comment
                tab_count = len(line) - len(line.lstrip('\t'))
                processed_lines.append('')
        
        # Fix comment formatting: ensure space after //
        if stripped.startswith('//') and len(stripped) > 2:
            # Check if there's no space after //
            if stripped[2] != ' ':
                # Get the indentation of the original line
                indent = line[:len(line) - len(line.lstrip())]
                # Add space after //
                fixed_comment = '//' + ' ' + stripped[2:]
                line = indent + fixed_comment
        
        processed_lines.append(line)
        
         # Only process if not in Javadoc, not in static block, and line ends with }
        if (not in_javadoc and not in_static_block and 
            (stripped.endswith('}') or stripped == '}')):
            
            # Check if we already added an empty line (check the last line in processed_lines)
            last_added_line = processed_lines[-1] if processed_lines else ""
            last_added_is_empty = last_added_line.strip() == ""
            
            # Check if the immediate next line exists
            if (i + 1 < len(lines)):
                next_line = lines[i + 1]
                next_stripped = next_line.strip()
                
                # NEW: Check for .append( pattern
                # Pattern: prev line contains .append( -> current line is } -> next line contains .append(
                if (i > 0 and i + 1 < len(lines) and
                    '.append(' in lines[i-1] and  # Previous line contains .append(
                    stripped == '}' and  # Current line is just }
                    '.append(' in lines[i+1]):  # Next line contains .append(
                    # Don't add empty line for this pattern
                    pass
                # NEW: Check for NpcStringId pattern
                # Pattern: prev line starts with NpcStringId. -> current line is } -> next line is // NpcStringId. -> line after is NpcStringId.
                elif (i > 0 and i + 2 < len(lines) and
                    lines[i-1].strip().startswith('NpcStringId.') and  # Previous line starts with NpcStringId.
                    stripped == '}' and  # Current line is just }
                    lines[i+1].strip().startswith('// NpcStringId.') and  # Next line is // NpcStringId.
                    lines[i+2].strip().startswith('NpcStringId.')):  # Line after comment starts with NpcStringId.
                    # Don't add empty line for this pattern
                    pass
                # NEW: Check if we're inside an array context - removed due to performance issues
                # elif is_inside_array_context(lines, i):
                #     # Don't add empty line inside arrays
                #     pass
                # NEW: Check if next line is @formatter comment
                elif is_formatter_comment(next_line):
                    pass  # Don't add empty line before @formatter comments
                # If we already added an empty line, don't add another
                elif last_added_is_empty:
                    pass  # Already have an empty line
                # If next line is already empty/whitespace-only, don't add anything
                elif next_stripped == '':
                    pass  # Next line is already empty
                # If next line is modifier/fallthrough comment, don't add empty line
                elif is_modifier_comment(next_line):
                    pass  # Don't add empty line before modifier/fallthrough comments
                # If next line is a control structure, comment, or special case, don't add empty line
                elif (is_control_structure(next_line) or 
                      is_comment(next_line) or 
                      next_stripped in {'{', '}', "});", "};", "}.execute();"}):
                    pass  # Don't add empty line before these
                else:
                    # Special case: Check if we have return; or continue; followed by closing bracket
                    # Pattern: } -> return; -> } OR } -> continue; -> }
                    if (i + 2 < len(lines) and 
                        (lines[i + 1].strip() == 'return;' or lines[i + 1].strip() == 'continue;') and 
                        (lines[i + 2].strip() == '}' or lines[i + 2].strip() == '});')):
                        # Don't add empty line in this pattern
                        pass
                    else:
                        # Look ahead to see if there's meaningful content that needs separation
                        check_idx = i + 1
                        should_add = False
                        found_formatter = False
                        
                        # First, do a quick scan for @formatter comments in the next few lines
                        for scan_idx in range(i + 1, min(i + 6, len(lines))):  # Look ahead max 5 lines
                            if is_formatter_comment(lines[scan_idx]):
                                found_formatter = True
                                break
                        
                        # If we found a @formatter comment nearby, don't add empty line
                        if found_formatter:
                            should_add = False
                        else:
                            while check_idx < len(lines):
                                check_line = lines[check_idx].strip()
                                if check_line == '':
                                    # Found an empty line, so don't add another
                                    break
                                elif is_formatter_comment(lines[check_idx]):
                                    # Don't add empty line before @formatter comments
                                    break
                                elif is_modifier_comment(lines[check_idx]):
                                    # Don't add empty line before modifier/fallthrough comments
                                    break
                                elif is_control_structure(lines[check_idx]) or is_comment(lines[check_idx]):
                                    # Skip control structures and comments
                                    check_idx += 1
                                    continue
                                elif check_line in {'{', '}', "});", "};", "}.execute();"}:
                                    # Don't add empty line before these
                                    break
                                else:
                                    # Found real content that needs separation
                                    should_add = True
                                    break
                        
                        if should_add:
                            tab_count = len(line) - len(line.lstrip('\t'))
                            processed_lines.append('')
        
        i += 1
    
    # Preserve the input file's line endings (CRLF or LF)
    line_ending = '\r\n' if '\r\n' in content else '\n'
    
    # Write with UTF-8 encoding (no BOM)
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.write(line_ending.join(processed_lines))
        if processed_lines:
            f.write(line_ending)

def process_directory(input_dir, output_dir):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.java', '.cs', '.c', '.cpp', '.h', '.hpp', '.ixx')):
                # Skip Config.java files
                if file == 'Config.java':
                    print(f'Skipped: {os.path.join(root, file)} (Config.java files are excluded)')
                    continue
                    
                input_path = os.path.join(root, file)
                relative_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, relative_path)
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                process_java_file(input_path, output_path)
                print(f'Processed: {input_path}')

def process_workspace_files(workspace_dir, target_names):
    """Process specific files by name across all workspace projects, in place."""
    count = 0
    for root, _, files in os.walk(workspace_dir):
        for file in files:
            if file in target_names:
                file_path = os.path.join(root, file)
                process_java_file(file_path, file_path)
                print(f'Processed: {file_path}')
                count += 1
    print(f'Processing complete. {count} files processed.')

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        # Filenames given: process them in place across all workspace projects
        process_workspace_files(os.path.dirname(os.path.abspath(__file__)), set(sys.argv[1:]))
    else:
        input_folder = 'input'
        output_folder = 'output'

        if not os.path.exists(input_folder):
            print(f'Error: Input folder "{input_folder}" does not exist.')
        else:
            process_directory(input_folder, output_folder)
            print('Processing complete.')