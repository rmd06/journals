'''
Appends README in each directory with JNL file string documenation.
Updates documentation if already present.
'''

from xml.dom.minidom import parse
from textwrap import wrap
from os import listdir, curdir, sep
from os.path import splitext, join, isdir
from re import compile, DOTALL, search, sub

# Special string comment in README under which documentation will be written
WARNING = '<!-- content below automatically generated by ' + __file__ + ' -->'


class Journal(object):
    '''
    String representation of Metamorph 7 journal xml.
    '''
    def __init__(self, filename):
        self._dom = parse(filename)
        self.filename = filename
    
    def __repr__(self):
        return '<Journal: ' + self.filename + '>'
    
    def _get_description(self):
        desc = self._dom.getElementsByTagName('Description')[0].childNodes
        if desc == []:
            return ''
        return desc[0].data
    
    def _get_code(self):
        cb = self._dom.getElementsByTagName('CodeBlock')[0].childNodes
        code = []
        for entry in cb:
            code.append( getattr(self, '_' + entry.nodeName)(entry) )
        return '\n'.join(code)
    
    def _CodeBlock(self, node):
        condition = node.getAttributeNode('Condition').nodeValue
        ret = ''
        if condition == 'false':
            ret += 'else:\n'
        for entry in node.childNodes:
            ret += ' ' * 4
            ret += getattr(self, '_' + entry.nodeName)(entry)
            ret += '\n'
        return ret
    
    def _CommentEntry(self, node):
        if node.childNodes == []:
            return ''
        return '# ' + '\n# '.join(wrap(node.childNodes[0].data, 76))
    
    def _FunctionEntry(self, node):
        name = node.getAttributeNode('FunctionName').nodeValue
        ret = name.replace(' ', '_')
        ret += '('
        for entry in node.childNodes:
            if ret[-1] != '(':
                ret += ',\n'
                ret += ' ' * (len(name) + 1)
            ret += getattr(self, '_' + entry.nodeName)(entry)
        ret += ')'
        return ret
    
    def _Variable(self, node):
        ret = ''
        if node.getAttributeNode('OverrideVariable') == None:
            ret = node.getAttributeNode('Name').nodeValue
        else:
            ret = node.getAttributeNode('OverrideVariable').nodeValue
        if ret != '':
            ret += ' = '
        if node.childNodes != []:
            value = node.childNodes[0].data
            if node.getAttributeNode('Type') == 'String':
                # String the leading number from the string
                value = value.split(' ', 1)
                ret += value[1]
            else:
                ret += value
        return ret
    
    def _AssignVariableEntry(self, node):
        ret = node.getAttributeNode('VariableName').nodeValue
        ret += ' = '
        ret += node.getAttributeNode('Expression').nodeValue
        return ret
    
    def _TraceEntry(self, node):
        ret = 'Trace('
        ret += node.getAttributeNode('Expression').nodeValue
        ret += ')'
        return ret
    
    def _IfThenElseEntry(self, node):
        ret = 'if '
        ret += node.getAttributeNode('Expression').nodeValue
        ret += ':'
        for entry in node.childNodes:
            ret += ',\n'
            ret += ' ' * 4
            ret += getattr(self, '_' + entry.nodeName)(entry)
        return ret
    
    def _RunJournalEntry(self,node):
        ret = 'Run_Journal('
        ret += node.getAttributeNode('JournalName').nodeValue
        ret += ')'
        return ret
    
    description = property(_get_description)
    code = property(_get_code)


def jnl_as_strings(filename):
    """ Write journal object into string list """
    jnl = Journal(filename)
    out = []
    if jnl.description != '':
        out.append("'''")
        out.append('\n'.join(wrap(jnl.description, 78)))
        out.append("'''")
    out.append(jnl.code)
    return out

def jnl_directories(node):
    ''' filter directories to exclude .git '''
    return [dir for dir in listdir(node) if isdir(dir) and dir != '.git']

def jnl_files(node):
    ''' filter for .jnl files '''
    return [file for file in listdir(node) if splitext(file)[1] == '.jnl'
                                           or splitext(file)[1] == '.JNL']

if __name__ == '__main__':
    # Recurse first-level directories for journal files
    for dir in jnl_directories(curdir):
        print('Entering directory {0}...'.format(dir))
        doc = []
        doc.append(WARNING)
        doc.append('Source Code')
        doc.append('-----------')
        for file in jnl_files(dir):
            print('  {0}'.format(file))
            doc.append('{0}:'.format(file))
            doc.append('```python')
            doc += jnl_as_strings(dir + sep + file)
            doc.append('```')
            doc.append('')
        doc = '\n'.join(doc)
        
        # Check if README already has doc
        doc_pattern = compile(WARNING + '.*', DOTALL)
        with open(dir + sep + 'README.md', 'r') as f:
            readme = f.read()
            match_result = search(doc_pattern, readme)
        
        # Update README as necessary
        if match_result == None:
            with open(dir + sep + 'README.md', 'a') as f:
                f.write(doc)
            print('... created')
        else:
            try:
                readme_updated = doc_pattern.sub(doc, readme)
            except:
                # FIXME #3: invalid group reference from lib/sre_parse.pyc
                pass
            if readme_updated == readme:
                print('... up-to-date')
            else:
                with open(dir + sep + 'README.md', 'w') as f:
                    f.write(readme_updated)
                print('... updated')
        print('')
