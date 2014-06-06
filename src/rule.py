from bigsuds import ServerError
import f5
import f5.util

class Rule(object):
    __version = 11
    def __init__(self, name, definition=None, description=None, ignore_verification=None, lb=None):
        if lb is not None and not isinstance(lb, f5.Lb):
            raise ValueError('lb must be of type lb, not %s' % (type(lb).__name__))

        self._lb                  = lb
        self._name                = name
        self._definition          = definition
        self._description         = description
        self._ignore_verification = ignore_verification

        if lb:
            self._set_wsdl()

    def __repr__(self):
        return "f5.Rule('%s')" % (self._name)

    def _set_wsdl(self):
        self.__wsdl = self._lb._transport.LocalLB.Rule

    @f5.util.lbmethod
    def _query_rule(self):
        return self.__wsdl.query_rule([self._name])[0]

    @f5.util.lbmethod
    def _get_description(self):
        return self.__wsdl.get_description([self._name])[0]

    @f5.util.lbmethod
    def _get_ignore_verification(self):
        return self.__wsdl.get_ignore_verification([self._name])[0]

    @f5.util.lbwriter
    def _modify_rule(self, value):
        self.__wsdl.modify_rule([value])

    @f5.util.lbwriter
    def _set_description(self, value):
        self.__wsdl.set_description([self._name], [value])

    @f5.util.lbwriter
    def _set_ignore_verification(self, value):
        self.__wsdl.set_ignore_verification([self._name], [value])

    @f5.util.lbwriter
    def _create(self):
        ruledef = {'rule_name': self._name, 'rule_definition': self._definition}
        self.__wsdl.create([ruledef])

    @f5.util.lbwriter
    def _delete(self):
        self.__wsdl.delete([self._name])

    ###########################################################################
    # Properties
    ###########################################################################
    @property
    def lb(self):
        return self._lb

    @lb.setter
    def lb(self, value):
        if value is not None and not isinstance(value, f5.Lb):
            raise ValueError('lb must be of type lb, not %s' % (type(value).__name__))
        self._lb = value
        self._set_wsdl()

    #### name ####
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self,value):
        if self._lb:
            raise AttributeError("set attribute name not allowed when linked to lb")
        self._name = name

    #### definition ####
    @property
    def definition(self):
        if self._lb:
            self._definition = self._query_rule()['rule_definition']
        return self._definition

    @definition.setter
    def definition(self, value):
        if self._lb:
            ruledef = {'rule_name': self._name, 'rule_definition': value}
            self._modify_rule(ruledef)
        self._definition = value

    #### description ####
    @property
    def description(self):
        if self._lb:
            self._description = self._get_description()
        return self._description

    @description.setter
    def description(self, value):
        if self._lb:
            self._set_description(value)
        self._description = value

    #### ignore_verification ####
    @property
    def ignore_verification(self):
        if self._lb:
            ignore_verification = self._get_ignore_verification()
            if ignore_verification == 'STATE_ENABLED':
                self._ignore_verification = True
            elif ignore_verification == 'STATE_DISABLED':
                self._ignore_verification = False
            else:
                raise RuntimeError(
                        'unknown ignore_verification_status %s received for Rule' % (ignore_verification))

        return self._ignore_verification

    @ignore_verification.setter
    def ignore_verification(self, value):
        if value == True:
            ignore_verification = 'STATE_ENABLED'
        elif value == False:
            ignore_verification = 'STATE_DISABLED'
        else:
            raise ValueError('ignore_verification must either True or False')

        if self._lb:
            self._set_ignore_verification(ignore_verification)

        self._ignore_verification = value

    ###########################################################################
    # Public API
    ###########################################################################
    def exists(self):
        try:
            self._get_description()
        except ServerError as e:
            if 'was not found' in e.message:
                return False
            else:
                raise
        except:
            raise

        return True

    @f5.util.lbtransaction
    def save(self):
        """Save the rule to the lb"""

        if not self.exists():
            if self._rule_definition is None or self._name is None:
                raise RuntimeError('name and definition must be set on create')
            self.create()
        elif self._definition is not None:
            self.definition = self._definition

        if self._description is not None:
            self.description = self._description
        if self._ignore_verification is not None:
            self.ignore_verification = self._ignore_verification

    def refresh(self):
        """Update all attributes from the lb"""
        self.definition
        self.description
        self.ignore_verification
    
    def delete(self):
        """Delete the rule from the lb"""
        self._delete_rule()
