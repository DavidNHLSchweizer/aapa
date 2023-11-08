from general.config import ListValueConvertor, config

def init_config():
    config.register('names', 'tussen', ListValueConvertor)
    config.init('names', 'tussen', ['van', 'de', 'der', 'den', 'te', 'in'])
init_config()

class Names:
    @staticmethod
    def tussenvoegsels()->list[str]:
        return config.get('names', 'tussen')
    @staticmethod
    def first_name(full_name: str)->str:
        if full_name and (words := full_name.split(' ')):
            return words[0]
        return ''
    @staticmethod
    def tussen(full_name: str, first_name='')->str:
        voegsels=Names.tussenvoegsels()
        words = full_name.split(' ')
        start_last_name = Names.__get_nr_first_name_words(full_name, first_name)
        tussen_words = []
        while start_last_name < len(words) and words[start_last_name] in voegsels:
            tussen_words.append(words[start_last_name])
            start_last_name+= 1
        return ' '.join(tussen_words)
    @staticmethod
    def __get_nr_first_name_words(full_name: str, first_name='')->int:
        words = full_name.split(' ')
        first = words[0]
        voegsels = Names.tussenvoegsels()
        result = 1
        while result < len(words) and len(first) < len(first_name):
            if words[result] in voegsels:
                break
            first  = first + ' ' + words[result]
            result += 1
        if result < len(words):
            return result
        return 1
    @staticmethod
    def last_name(full_name: str, first_name='', include_tussen: bool=True):
        if full_name and (words := full_name.split(' ')):
            start = Names.__get_nr_first_name_words(full_name,first_name)
            voegsels = Names.tussenvoegsels()
            if not include_tussen: 
                while words[start] in voegsels and start < len(words)-1:
                    start +=1
            return ' '.join(words[start:len(words)])
        return ''   
    @staticmethod
    def initials(full_name: str='', email: str = '')->str:
        result = ''
        if email:
            for word in email[:email.find('@')].split('.'):
                result += word[0]
        elif full_name:            
            for word in full_name.split(' '):
                result += word[0]
        return result.lower()


