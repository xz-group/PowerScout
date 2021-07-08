import pyparsing as pp
import copy
import re


class ParserBasic:
    @staticmethod
    def _plain_text(text):
        text = re.sub('[/_()~]', '', text)
        text = re.sub('^[\-]|[\-]$', "N", text)
        text = re.sub('^[\+]|[+]$', "P", text)
        text = re.sub('[\-+]', "", text)
        text = re.sub('(P5V[0-9])$', "P5V", text)
        text = re.sub('(GND[0-9])$', "GND", text)
        return text


class Sheet:
    def __init__(self, sheet):
        self.number = sheet.num
        self.name = sheet.name
        self.time_stamp = sheet.tstamps
        self.title = sheet.title
        self.company = sheet.company
        self.revision_number = sheet.rev
        self.created_date = sheet.date
        self.source_file = sheet.source
        self.comments = ""
        for i in range(len(sheet.comments)):
            if sheet.comments[i].text is not "":
                self.comments = self.comments + sheet.comments[i].text + '\n'
        # len(sheet.comments)  #: Number of comments for the schematic sheet.
        # sheet.comments[0].num  #: Number of the comment.
        # sheet.comments[0].text  #: Text of the comment.


class Library:
    def __init__(self, library):
        self.name = library.name
        self.file_location = library.uri  # File location of the library.


class Field:
    def __init__(self, part_type_field):
        self.name = part_type_field.name  # Name of the field of the part.
        self.value = part_type_field.value  # Value assigned to the field of the part.


class PartTypePin(ParserBasic):
    def __init__(self, part_type_pin=None, number=None, net=None):
        if part_type_pin is not None:
            self.number = part_type_pin.num  # Pin number of the pin of the part.
            self.name = self._plain_text(part_type_pin.name)  # Pin name of the pin of the part.
            self.type = part_type_pin.type  # Electrical type of the pin of the part.
            self.net = ''
        else:
            self.number = number
            self.net = net


class NetPin(ParserBasic):
    def __init__(self, net_pin):
        self.part_reference_designator = net_pin.ref  # Part reference designator for first pin on the net.
        self.pin_number_of_referenced_part = net_pin.num  # Pin number of referenced part for the pin on the net.


class PartType(ParserBasic):
    def __init__(self, part_type):
        self.lib_name = part_type.lib  # Library containing the part.
        self.name = self._plain_text(part_type.name)  # Part type name of the part.
        self.description = part_type.desc  # Description of the part.
        self.doc_filename = part_type.docs  # Document file name for the part.

        self._list_of_files = part_type.fields  # List of fields for the part.
        self.num_list_of_fields = len(part_type.fields)  # Number of fields for the part.
        self.fields = {}
        for i in range(self.num_list_of_fields):
            self.fields[part_type.fields[i].name] = Field(part_type.fields[i])
            # field = Field(part_type.fields[i])
            # self.fields[part_type.fields[i].name] = field

        self._list_of_pins = part_type.pins  # List of pins for the part.
        self.num_list_of_pins = len(part_type.pins)  # Number of pins on the part.
        self.pins = {}
        for i in range(self.num_list_of_pins):
            self.pins[part_type.pins[i].num] = PartTypePin(part_type.pins[i])
            # pin = PartTypePin(part_type.pins[i])
            # self.pins[part_type.pins[i].num] = pin

        self._list_of_footprints = part_type.footprints  # List of footprints for the part.
        self.num_list_of_footprints = len(part_type.footprints)  # Number of footprints for the part.
        self.footprints = []
        for i in range(self.num_list_of_footprints):
            self.footprints.append(part_type.footprints[i])  # footprint for the part

        self._list_of_aliases = part_type.aliases  # List of aliases for the part.
        self.num_list_of_aliases = len(part_type.aliases)  # List of aliases for the part.
        self.aliases = []
        for i in range(self.num_list_of_aliases):
            self.aliases.append(part_type.aliases[i])


class PartInstance(ParserBasic):
    def __init__(self, part_instance):
        self.reference_designator = part_instance.ref  #: Reference designator for the part.
        self.value = self._plain_text(part_instance.value)  #: Value of the part.
        self.time_stamp = part_instance.tstamp  #: Time stamp for the part.
        self.datasheet_file_location = part_instance.datasheet  #: File location of datasheet for the part.
        self.lib_name = part_instance.lib  #: Name of the library containing the part.
        self.name = self._plain_text(part_instance.name)  #: Part type name for the part.
        self.description = part_instance.desc  #: Description for the part.
        self.footprint = part_instance.footprint  #: PCB footprint for the part.
        self.sheet_name = part_instance.sheetpath.names  #: Sheet name on which the part appears.
        self.sheet_time_stamp = part_instance.sheetpath.tstamps  #: Time stamp for the sheet on which the part appears.
        self._list_of_fields = part_instance.fields  #: List of fields for the part.
        self.num_list_of_fields = len(part_instance.fields)  #: Number of fields for the part.
        self.fields = {}
        self.spice_line = ""
        for i in range(self.num_list_of_fields):
            self.fields[part_instance.fields[i].name] = Field(part_instance.fields[i])
            # field = Field(part_instance.fields[i])
            # self.fields[part_instance.fields[i].name] = field
        self.pins = {}


class Net(ParserBasic):
    def __init__(self, net):
        self.name = self._plain_text(net.name)  #: Name of the net.
        self.code = net.code  #: Code number for the net.
        if self.name is "":
            self.name = 'n' + str(self.code)
        self._list_of_net_pins = net.pins  #: List of pins attached to the net.
        self.num_list_of_net_pins = len(net.pins)  #: Number of pins attached to the net.
        self.net_pins = {}
        for i in range(self.num_list_of_net_pins):
            self.net_pins[i] = NetPin(net.pins[i])
            # net_pin = NetPin(net.pins[i])
            # self.net_pins[i] = net_pin


class KicadParser(ParserBasic):
    """
    The class that can parse the Kicad net files.
    And convert them to spice netlist.
    """

    def __init__(self, net_filepath):
        self.net_filepath = net_filepath
        self.circuit_name = self.net_filepath.split('\\')[-1]
        self._raw_net = ''
        self.read_net(self.net_filepath)
        self._net_database = self._net_file_parser(self._raw_net)
        self._assign_global_info()
        self._assign_sheet_info()
        self._assign_lib_info()
        self._assign_type_info()
        self._assign_instance_info()
        self._assign_net_info()
        self._instance_generate_spice_line()  # Generate spice line for each instance
        pass

    def read_net(self, net_filepath):
        try:
            self._raw_net = net_filepath.read()
        except Exception:
            try:
                self._raw_net = open(net_filepath, 'r', encoding='latin_1').read()
            except Exception:
                print("Error: Cannot openfile [{}], net is not updated.\n".format(net_filepath))

        return self._raw_net

    def _net_file_parser(self, raw_net=None):
        """
        Return a pyparsing object storing the contents of a KiCad netlist.
        """

        if raw_net is None:
            raw_net = self._raw_net
        # ++++++++++++++++++++++++++++ Parser Definition +++++++++++++++++++++++++++

        # Basic elements.
        word = pp.Word(pp.alphas)
        inum = pp.Word(pp.nums)
        string = pp.ZeroOrMore(pp.White()).suppress() + pp.CharsNotIn('()') + pp.ZeroOrMore(pp.White()).suppress()
        qstring = pp.dblQuotedString() ^ pp.sglQuotedString()
        qstring.addParseAction(pp.removeQuotes)
        anystring = pp.Optional(qstring ^ string)  # Don't know why Optional() is necessary to make the parser work.

        # Design section.
        source = self._paren_clause('source', pp.Optional(anystring)('source'))
        date = self._paren_clause('date', pp.Optional(anystring)('date'))
        tool = self._paren_clause('tool', pp.Optional(anystring)('tool'))
        number = self._paren_clause('number', inum('num'))
        name = self._paren_clause('name', anystring('name'))
        names = self._paren_clause('names', anystring('names'))
        tstamp = self._paren_clause('tstamp', anystring('tstamp'))
        tstamps = self._paren_clause('tstamps', anystring('tstamps'))
        title = self._paren_clause('title', pp.Optional(anystring)('title'))
        company = self._paren_clause('company', pp.Optional(anystring)('company'))
        rev = self._paren_clause('rev', pp.Optional(anystring)('rev'))
        txt = self._paren_clause('value', anystring('text'))
        comment = self._paren_clause('comment', pp.Group(number & txt))
        comments = pp.Group(pp.OneOrMore(comment))('comments')
        title_block = self._paren_clause('title_block', pp.Optional(title) &
                                         pp.Optional(company) & pp.Optional(rev) &
                                         pp.Optional(date) & pp.Optional(source) & comments)
        sheet = self._paren_clause('sheet', pp.Group(number + name + tstamps + pp.Optional(title_block)))
        sheets = pp.OneOrMore(sheet)('sheets')
        design = (self._paren_clause('design', pp.Optional(source) & pp.Optional(date) &
                                     pp.Optional(tool) & pp.Optional(sheets)))

        # Components section.
        ref = self._paren_clause('ref', anystring('ref'))
        value = self._paren_clause('value', anystring('value'))
        datasheet = self._paren_clause('datasheet', anystring('datasheet'))
        field = pp.Group(self._paren_clause('field', name & anystring('value')))
        fields = self._paren_clause('fields', pp.ZeroOrMore(field)('fields'))
        lib = self._paren_clause('lib', anystring('lib'))
        part = self._paren_clause('part', anystring('name'))
        footprint = self._paren_clause('footprint', anystring('footprint'))
        description = self._paren_clause('description', anystring('desc'))  # Gets used here and in libparts.
        libsource = self._paren_clause('libsource', lib & part & pp.Optional(description))
        sheetpath = pp.Group(self._paren_clause('sheetpath', names & tstamps))('sheetpath')
        comp = pp.Group(self._paren_clause('comp', ref & value & pp.Optional(datasheet) &
                                           pp.Optional(fields) & pp.Optional(libsource) & pp.Optional(footprint) &
                                           pp.Optional(sheetpath) & pp.Optional(tstamp)))
        components = self._paren_clause('components', pp.ZeroOrMore(comp)('parts'))

        # Part library section.
        docs = self._paren_clause('docs', anystring('docs'))
        pnum = self._paren_clause('num', anystring('num'))
        ptype = self._paren_clause('type', anystring('type'))
        pin = self._paren_clause('pin', pp.Group(pnum & name & ptype))
        pins = self._paren_clause('pins', pp.ZeroOrMore(pin))('pins')
        alias = self._paren_clause('alias', anystring('alias'))
        aliases = self._paren_clause('aliases', pp.ZeroOrMore(alias))('aliases')
        fp = self._paren_clause('fp', anystring('fp'))
        footprints = self._paren_clause('footprints', pp.ZeroOrMore(fp))('footprints')
        libpart = pp.Group(self._paren_clause('libpart', lib & part & pp.Optional(
            fields) & pp.Optional(pins) & pp.Optional(footprints) & pp.Optional(aliases) &
                                              pp.Optional(description) & pp.Optional(docs)))
        libparts = self._paren_clause('libparts', pp.ZeroOrMore(libpart))('libparts')

        # Libraries section.
        logical = self._paren_clause('logical', anystring('name'))
        uri = self._paren_clause('uri', anystring('uri'))
        library = pp.Group(self._paren_clause('library', logical & uri))
        libraries = self._paren_clause('libraries', pp.ZeroOrMore(library))('libraries')

        # Nets section.
        code = self._paren_clause('code', inum('code'))
        part_pin = self._paren_clause('pin', anystring('num'))
        node = self._paren_clause('node', pp.Group(ref & part_pin))
        nodes = pp.Group(pp.OneOrMore(node))('pins')
        net = self._paren_clause('net', pp.Group(code & name & nodes))
        nets = self._paren_clause('nets', pp.ZeroOrMore(net))('nets')

        # Entire Netlist.
        version = self._paren_clause('version', word('version'))
        end_of_file = pp.ZeroOrMore(pp.White()) + pp.stringEnd
        parser = self._paren_clause('export', version +
                                    (design & components & pp.Optional(libparts) & pp.Optional(libraries) & nets
                                     )) + end_of_file.suppress()

        return parser.parseString(raw_net)

    @staticmethod
    def _paren_clause(keyword, subclause):
        """
        Create a parser for a parenthesized list with an initial keyword.
        """
        lp = pp.Literal('(').suppress()
        rp = pp.Literal(')').suppress()
        kw = pp.CaselessKeyword(keyword).suppress()
        clause = lp + kw + subclause + rp
        return clause

    def _assign_global_info(self):
        # Global Netlist Information:
        self.net_format_version = self._net_database.version

        # Global Design Information:
        self.sch_filename = self._net_database.source
        self.sch_created_date = self._net_database.date
        self.sch_created_tool = self._net_database.tool

    def _assign_sheet_info(self):
        # Schematic Sheet Information:
        self._list_of_sheets = self._net_database.sheets
        self.num_list_of_sheets = len(self._net_database.sheets)
        self.sheets = {}
        for i in range(self.num_list_of_sheets):
            self.sheets[self._net_database.sheets[i].num] = Sheet(self._net_database.sheets[i])
            # sheet = Sheet(self._net_database.sheets[i])
            # self.sheets[self._net_database.sheets[i].num] = sheet

    def _assign_lib_info(self):
        # Library Information:
        self._list_of_libs = self._net_database.libraries  #: List of libraries used in the netlist.
        self.num_list_of_libs = len(self._net_database.libraries)  #: Number of libraries in the list.
        self.libs = {}
        for i in range(self.num_list_of_libs):
            self.libs[self._net_database.libraries[i].name] = Library(self._net_database.libraries[i])
            # lib = Library(self._net_database.libraries[i])
            # self.libs[self._net_database.libraries[i].name] = lib

    def _assign_type_info(self):
        # Library of Components:
        self._list_of_part_types = self._net_database.libparts  #: List of part types used in the netlist.
        self.num_list_of_part_types = len(self._net_database.libparts)  #: Number of part types in the list.
        self.part_types = {}
        for i in range(self.num_list_of_part_types):
            self.part_types[self._plain_text(self._net_database.libparts[i].name)] = PartType(
                self._net_database.libparts[i])
            # part_type = PartType(self._net_database.libparts[i])
            # self.part_types[self._net_database.libparts[i].name] = part_type

    def _assign_instance_info(self):
        # Parts:
        self._list_of_part_instances = self._net_database.parts  #: List of part instances used in the netlist.
        self.num_list_of_part_instances = len(self._net_database.parts)  #: Number of parts used in the list.
        self.part_instances = {}
        for i in range(self.num_list_of_part_instances):
            # if self._net_database.parts[i].ref in self.part_instances.keys():
            #     self._net_database.parts[i].ref = self._net_database.parts[i].ref + str(i)
            self.part_instances[self._net_database.parts[i].ref] = PartInstance(self._net_database.parts[i])
            # part_instance = PartInstance(self._net_database.parts[i])
            # self.part_instances[self._net_database.parts[i].ref] = part_instance
        for designator in self.part_instances:
            try:
                self.part_instances[designator].pins = copy.deepcopy(
                    self.part_types[self.part_instances[designator].name].pins)
                for pin in self.part_instances[designator].pins:
                    self.part_instances[designator].pins[pin].net = designator + '_' + pin
            except KeyError:
                self.part_instances[designator].pins = {}

    def _assign_net_info(self):
        # Nets Connections:
        self._list_of_nets = self._net_database.nets  #: List of nets connecting the component pins.
        self.num_list_of_nets = len(self._net_database.nets)  #: Number of nets in the list.
        self.nets = {}
        for i in range(self.num_list_of_nets):
            if self._net_database.nets[i].name is "":
                self.nets['net_' + str(self._net_database.nets[i].code)] = Net(self._net_database.nets[i])
                # net = Net(self._net_database.nets[i])
                # self.nets['n-' + str(self._net_database.nets[i].code)] = net
            else:
                self.nets[self._plain_text(self._net_database.nets[i].name) + '_' + str(
                    self._net_database.nets[i].code)] = Net(self._net_database.nets[i])
                # net = Net(self._net_database.nets[i])
                # self.nets[self._net_database.nets[i].name + '-' + str(self._net_database.nets[i].code)] = net
        pass
        # Assign Nets Connections to Part Instances:
        for net in self.nets:
            for pin in self.nets[net].net_pins.values():
                designator = pin.part_reference_designator
                pin_number = pin.pin_number_of_referenced_part
                try:
                    self.part_instances[designator].pins[pin_number].net = self.nets[net].name
                except KeyError:
                    self.part_instances[designator].pins[pin_number] = PartTypePin(number=pin_number,
                                                                                   net=self.nets[net].name)

    def _instance_generate_spice_line(self):
        for designator in self.part_instances:
            spice_line = ""
            if re.match('^[RLC]', designator, re.I):
                instance_title = designator
                instance_value = self.part_instances[designator].value
            else:
                instance_title = 'X' + designator
                if self.part_instances[designator].value == self.part_instances[designator].name:
                    instance_value = self.part_instances[designator].value
                else:
                    instance_value = self.part_instances[designator].value + '_' + self.part_instances[designator].name
            for i in range(len(self.part_instances[designator].pins)):
                try:
                    spice_line = spice_line + ' ' + self.part_instances[designator].pins[str(i + 1)].net
                except KeyError:
                    print(spice_line)
            self.part_instances[designator].spice_line = instance_title + ' '.join([spice_line, instance_value])

    def generate_spice_netlist(self):
        # title = self.sch_filename
        # try:
        #     title = title.split('/')
        # except TypeError:
        #     title = self.net_filepath
        #     title = title.split('\\')
        title = self.circuit_name
        spice = ' '.join(['.title', title, '\n'])
        lib_line_front = ".include"
        # lib_line_main = "subckt.lib"
        lib_line_main = self.net_filepath.split('\\')[0:-1]
        lib_line_main[-2] = "TRIT_Benchmarks_Spice"
        lib_line_main.append("subckt.lib")
        lib_line_main = '\\'.join(lib_line_main)
        lib_line = ' '.join([lib_line_front, lib_line_main])
        spice = spice + lib_line + '\n'
        for designator in self.part_instances:
            spice_line = self.part_instances[designator].spice_line
            spice = spice + spice_line + '\n'
        spice = spice + '.end' + '\n'
        return spice
