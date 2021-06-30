from xml.etree import ElementTree
import re
from synthesizer import Synthesizer, Waveform, Writer, Player
import random

class Mscx:
    def __init__(self, path, bpm=180) -> None:
        self.bpm = bpm
        
        self.tree = ElementTree.parse(path)
        self.root = self.tree.getroot()
        
        self.staff_ary = self.root.findall('Score')[0].findall('Staff')
        self.l = None
        if len(self.staff_ary) > 1:
            self.r, self.l = self.staff_ary
        else:
            self.r = self.staff_ary[0]
            
        # right hand score
        self.r_score = []
        for m in self.r.findall('Measure'):
            self.r_score.append(self.measure_elem_to_ary(m))
        self.r_score_playable = self.handle_tie(self.r_score)
        
        # left hand score
        if self.l_exists():
            self.l_score = []
            for m in self.l.findall('Measure'):
                self.l_score.append(self.measure_elem_to_ary(m))
            self.l_score_playable = self.handle_tie(self.l_score)

        self.player = Player()
        self.player.open_stream()   
        
    def l_exists(self):
        return self.l is not None     
        
    def measure_elem_to_ary(self, measure):
        """
        @param measure {Element 'Measure}
        @return {array} tupples of notes info in array
        """
        self.v = measure.find('voice')
        
        self.notes_elem_ary = []
        for e in self.v.findall('*'):
            if e.tag == 'Chord' or e.tag == 'Rest' or \
                e.tag == 'Tuplet' or e.tag == 'endTuplet':
                self.notes_elem_ary.append(e)
        
        self.notes_ary = []
        self.tuplet_mode = False
        self.normalNotes = None # for tuplet
        self.actualNotes = None # for tuplet
        for e in self.notes_elem_ary:
            if e.find('durationType') != None:
                self.duration = e.find('durationType').text
            if self.tuplet_mode:
                self.duration += '*{}/{}'.format(self.normalNotes, self.actualNotes)
            if e.tag == 'endTuplet':
                self.tuplet_mode = False
            elif e.tag == 'Tuplet':
                self.normalNotes = e.find('normalNotes').text
                self.actualNotes = e.find('actualNotes').text
                self.tuplet_mode = True
            elif e.tag == 'Rest':
                self.notes_ary.append([self.duration, 0])
            else: # 'Chode'
                if e.find('dots') != None:
                    self.duration += '.'
                self.n = e.find('Note')
                self.pitch = int(self.n.find('pitch').text)
                
                self.spanner_ary = self.n.findall('Spanner')
                if self.spanner_ary != []:
                    for spanner in self.spanner_ary:    
                        if spanner.find('prev') != None:
                            self.duration = '_' + self.duration
                
                self.notes_ary.append([self.duration, self.pitch])
        return self.notes_ary
    
    def handle_tie(self, score):
        """
        remove tie, shorten measures
        """
        for i in reversed(range(1, len(score))):
            for j in reversed(range(len(score[i]))):
                self.str_len = score[i][j][0]
                if self.str_len[0] == '_':
                    self.tpl = score[i].pop(j)
                    if j==0:
                        score[i-1][-1][0] += ('=' + self.tpl[0][1:])
                    else:
                        score[i][j-1][0] += ('=' + self.tpl[0][1:])
                        
        score = [e for e in score if e != []]
        return score
    
    def get_len_from_dict(self, length):
        dict = {'16th': 1/16, 'eighth': 1/8, 'quarter': 1/4, 'half': 1/2, 'whole': 1}

        if length in dict:
            return dict[length]
        
        self.len_ary = re.split('\*|/', length)
        return dict[self.len_ary[0]] * int(self.len_ary[1]) / int(self.len_ary[2])

    def sa(self, length, pitch):
        """
        @param length {string} ex. 'quarter'
        @param pitch {int} 60 => C4
        """
        # handle length
        self.sum_len = 0
        
        self.len_ary = length.split('=')
        for len_e in self.len_ary:
            self.quarter_len = 60 / self.bpm * 4
            if len_e[-1] == '.':
                self.quarter_len *= 1.5
                len_e = len_e[:-1]
            self.quarter_len *= self.get_len_from_dict(len_e)
            self.sum_len += self.quarter_len
        
        # handle pitch
        self.f = 0.
        if pitch > 0: self.f = 440 * 2**((pitch-69)/12)
        
        self.synth = Synthesizer(osc1_waveform=Waveform.triangle,
                                 osc1_volume=0.2,
                                 use_osc2=False, # if true, osc1_volume is set to 1.0 ?
                                 osc2_volume=0.1,
                                 osc2_freq_transpose=1.5)
        self.player.play_wave(self.synth.generate_constant_wave(self.f, self.sum_len))

    def play(self, hand='right'):
        """
        play score (default right hand score)
        """
        self.score_playable = None
        if hand == 'right':
            self.score_playable = self.r_score_playable
        elif hand == 'left' and self.l_exists():
            self.score_playable = self.l_score_playable
            
        if self.score_playable is None:
            print('There is no score for left hand.')
            print('usage: mscx.play(hand=\'right\')')
            return
        for measure in self.score_playable:
            for note in measure:
                self.sa(note[0], note[1])

def beep_bit(num=-1):
    score = [
        ('Venus', 75),
        ('Alatreon', 180),
        ('Torneko', 80),
        ('Ozorani', 140),
        ('Dog_song', 110),
        ('Rhapsody', 130),
        ('Almenian', 120),
        ('Sorahe', 90)
    ]
    
    if num == -1:
        r = random.randint(0, len(score)-1)
        num = r
    
    m = Mscx('/Users/oomiyanaoki/code/venus/score/'+score[num][0]+'.mscx', bpm=score[num][1])
    m.play()
