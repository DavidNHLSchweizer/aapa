""" Simple class to generate random students """
import datetime
import random
import string
from data.classes.aanvragen import Aanvraag
from data.classes.bedrijven import Bedrijf
from data.classes.files import File
from data.classes.studenten import Student
from data.general.const import FileType, MijlpaalType
from general.singleton import Singleton
from storage.aapa_storage import AAPAStorage


#https://degoudenuil.nl/motivatie-quotes/
gouden_uil_quotes = [
    "Een dag hoeft nooit helemaal goed te zijn, maar er zit altijd iets goeds in de dag", 
    "If you don't get what you want, choose to want what you get", 
    "Never get so busy making a living that you forget making a life", 
    "Verwacht minder. Krijg meer", 
    "Don't worry about the failures, worry about the chances you miss when you don't try", 
    "Forget all the reasons why it won't work and believe the one reason why it will", 
    "If we wait till we're ready, we'll be waiting for the rest of our lives",  #(Lemony Snicket)
    "Don't be afraid your life will end, be afraid it will never start", 
    "Life begins at the end of your comfort zone", 
    "Success is not final, failure is not fatal; it is the courage to continue that counts",  #(Winston Churchill)
    "You never look back thinking 'I failed too much'. You look back thinking 'I didn't try enough", 
    "Accept the things you cannot change, and change the things you cannot accept", 
    "Everything you've ever wanted is on the other side of fear",  #(George Addair)
    "Het gevolg van een ruzie is vaak erger dan de oorzaak ervan", 
    "Nothing comes without friction", 
    "Sometimes good things fall apart so better things can fall together", 
    "Je kunt de kracht van een relatie soms pas zien als die voorbij is", 
    "Een vogel is nooit bang dat zijn tak breekt, want hij vertrouwt niet op de tak maar op zijn vleugels", 
    "Zelfvertrouwen ontstaat niet omdat je altijd gelijk hebt. Maar omdat je niet bang bent ongelijk te hebben", 
    "You don't have to be different to make a difference", 
    "Excellence sucks. Perfection doesn't exist. Be outstanding", 
    "Compare yourself to who you were yesterday instead of comparing yourself of who someone else is today", 
    "Everything will be okay in the end. If it isn't ok, then it's not the end…", 
    "Believe you can and you're halfway there",  #(Theodore Roosevelt)
    "Feedback; always take it serious, never take it personal",  #(Bill Clinton)
    "Een opgever wint nooit en een winnaar geeft nooit op", 
    "Life is like a glowstick: you have to break before you can shine", 
    "When one door of happiness closes, another opens. But often we look so long at the closed door that we do not see the one that has been opened for us",  #(Helen Keller)
    "When life puts you in tough positions, don't say 'why me?' but 'try me!'", 
    "Dreams don't come true because people get lucky. People get lucky because they don't give up", 
    "There are people who prefer to say 'yes' and there are people who prefer to say 'no'. Those who say 'yes' are rewarded by the adventures they have. Those who say 'no' are rewarded by the safety they attain",  #(Keith Johnstone)
    "The better your awareness, the better the choices. As you make better choices, you will see better results", 
    "If you can't decide what to do, get on the road. You won't find the answer. It will find you", 
    "Nee zeggen tegen anderen is ja zeggen tegen jezelf", 
    "Als je moeilijke keuzes durft te maken wordt je leven makkelijker. Als je alleen maar makkelijke keuzes durft te maken wordt je leven moeilijker",  #(Eelco de Boer)
    "Je hoeft niet alles meteen goed te doen, maar je moet iets doen voordat het goed gaat", 
    "Doubt kills more dreams than failure ever will", 
    "In the end we only regret the chances we didn't take",  #(Lewis Carroll)
    "The best time to plant a tree was 20 years ago. The second best time is now", 
    "A year from now you will wish you had started today",  #(Karen Lb)
    "Don't wait for the perfect moment. Be the moment and make it perfect", 
    "It's not about being perfect. It's about being authentic", 
    "Perfection is the lowest standard, because you will never reach it. Go for outstanding", 
    "Success without fulfilment is failure", 
    "Never be a prisoner of your past, but be an architect of your future", 
    "It would'nt be a shame if you're not succeeding. But it would be a shame if you didn't try", 
    "Be awesome not perfect", 
    "Dreams can come true. If you have the courage to pursue them",  #~Walt Disney
    "What you can do today, can improve all your tomorrow", 
    "Those who have a why to live, can handle almost every how", 
    "Today is the first day for the rest of your life", 
    "Een winnaar heeft een plan, een verliezer een excuus", 
    "If you never try, you never know", 
    "Success is getting what you want, happiness is wanting what you get",  #~W.P. Kinsella
    "Geluk is heel graag willen wat je al hebt", 
    "In order to succeed, your desire for success should be greater than your fear of failure", 
    "A goal is a dream with a deadline",  #~Napoleon Hill
    "Do not become a seeker for success become a person of value", 
    "Mensen die haast hebben gaan niet sneller, ze kijken alleen moeilijker", 
    "A person's success can easily be measures by the number of uncomfortable moments he or she is willing to have", 
    "The greater danger for most of us is not that our aim is too high and we miss it, but that it is too low and we hit it",  #~Michelangelo
    "I've missed more than 9000 shots in my career. I've lost almost 300 games. 26 times I've been trusted to take the game winning shot and missed. I've failed over and over and over again in my life. And that is why I succeed",  #~Michael Jordan
    "Hard work beats talent. However, hard work in areas of your talent will make you unstoppable", 
    "Work so hard that one day your signature will be called an autograph", 
    "Je krijgt niet wat je verdient maar waar je bereid bent voor te werken", 
    "Sell what people want, and give what people need", 
    "If you look at what you have in life, you'll always have more. If you look at what you don't have in life, you'll never have enough",  #(Oprah Winfrey)
    "Verkopen is de klant helpen met inkopen", 
    "To find the right customers you sometimes have to say no to the wrong customers", 
    "Passion is the genisis of genius", 
    "Als je snel wilt gaan doe je het alleen, als je ver wilt gaan doe je het samen", 
    "If you think it's expensive to hire a professional to do the job, wait until you hire an amateur", 
    "You don't get paid by the hour, you get paid by the value you bring", 
    "The more you learn, the more you earn",  #~Warren Buffet
    "Life is about making an impact, not making an income",  #~Kevin Kruse
    "Lack of motivation? You problem is not motivation. Your problem is you don't have a large enough vision", 
    "Why have two plans? You only have one life. Don't put your hopes and dreams into plan B. If doing something is the right thing, make plan A work", 
    "Life is not measured by the number of breath we take, but by the moments that take our breath away", 
    "Growth is painful. Change is painful. But nothing is as painful as staying stuck somewhere you don't belong",  #~Mandy Hale
    "The number one reason people don't get what they want is that they don't know what they want", 
    "Definiteness of purpose is the starting point of all achievement",  #~W. Clement Stone
    "The two most important days in your life are the day you are born and the day you find out why",  #~Mark Twain
    "Build your own dreams, or someone else will hire you to build theirs",  #~Farrah Gray
    "Hoe belangrijker een roeping is, hoe meer weerstand we zullen voelen om ermee door te gaan omdat er nogal wat op het spel staat. We zijn doodsbenauwd dat we het straks zullen verpesten als we er echt voor gaan",  #~Steven Pressfield
    "The purpose of life is a life with purpose",  #~Robert Byrne
    "More important than achievement is direction. If you keep on going in the right direction, you will achieve your dreams",  #~Tony Robbins
    "There's always something you can do today to get you closer to your dreams tomorrow", 
    "The first step to get anywhere, is deciding you're not willing to stay where you are", 
    "The quieter you become, the more you can hear", 
]

class RandomData(Singleton):
    def __init__(self, storage: AAPAStorage):
        self.storage = storage
        self.students = self._get_students({Student.Status.AANVRAAG, Student.Status.BEZIG})
        self.bedrijven = self._get_bedrijven()
        self.dates = self._get_dates()
        # self.files= self._get_files()
    def _get_students(self, status: set[Student.Status])->list[Student]:
        if (ids := self.storage.queries('studenten').find_ids_where('status', status)):
            return self.storage.read_many('studenten', set(ids))
        return []    
    def _get_files(self)->list[File]:
        return self.storage.queries('files').find_all()
    def random_student(self)->Student:
        return random.choice(self.students)
    def random_aanvraag(self)->Aanvraag:
        kans = random.randrange(1,9)
        aanvraag = Aanvraag(student=self.random_student(), bedrijf=self.random_bedrijf(),
                        datum=self.random_date(),titel=self.random_quote(),kans=kans,versie=random.randrange(1,kans+1))        
        aanvraag.files.add(self.random_file(FileType.AANVRAAG_PDF, MijlpaalType.AANVRAAG))
        return aanvraag
    def _get_bedrijven(self)->list[Bedrijf]:
        return self.storage.queries('bedrijven').find_all()
    def random_bedrijf(self)->Bedrijf:
        return random.choice(self.bedrijven)
    def random_file(self, filetype: File.Type, mijlpaal_type: MijlpaalType)->File:
        return File(self.random_filename(filetype.default_suffix()),filetype=filetype, mijlpaal_type=mijlpaal_type)
        # return random.choice(list(filter(self.files,key =lambda f: f.filetype==filetype)))
    def random_filename(self, suffix = '')->str:
        return ''.join(random.choices(string.ascii_uppercase +
                             string.digits, k=8))+suffix
    def _get_dates(self):
        result = []
        date = datetime.datetime(year=2020, month=1,day=1)
        date1 = datetime.datetime(year=2024, month=2,day=29)                
        while date <= date1:
            result.append(date)
            date += datetime.timedelta(days=1.33) 
        return result
    def random_date(self)->datetime.date:
        return random.choice(self.dates)
    def random_quote(self)->str:
        return random.choice(gouden_uil_quotes)
