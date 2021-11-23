import numpy as np
import pygame
import time
import mido

# seq2midi：将 seq 对应的音符序列转换成单轨道的 MIDI 文件，并返回
# 默认参数：C3 = 48, C4 = 60, C5 = 72, C6 = 84
# 默认节拍：4/4 拍, tempo=75bpm, key=C大调, 不调整音符强弱。
# npc:note_per_crotchets，每一个四分音符内演奏几个 seq 传入的乐音。npc = 4 时最小单元为 16 分音符，= 2 时为 8 分音符。

def seq2midi(seq,npc=4,tempo=75,key='C'):
    
    mid=mido.MidiFile()
    track=mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message('program_change', program=0)) # 大钢琴音色
    
    # tempo = mido.bpm2tempo(bpm)
    cpn = 1.0/npc # 每个 seq 中的音符对应了多少个四分音符
    meta_time=mido.MetaMessage('time_signature', numerator=4, denominator=4) # 4/4 拍
    meta_tempo=mido.MetaMessage('set_tempo', tempo = tempo, time=0)
    meta_tone=mido.MetaMessage('key_signature', key=key) # C 大调
    
    def playNote(note, len, delay=0):
        # delay 可以调整空拍子，暂时没有加上支持
        meta_time = 60 * 60 * 10 / tempo
        track.append(mido.Message('note_on', note=note, velocity=64, time=round(delay*meta_time)))
        track.append(mido.Message('note_off', note=note, velocity=64, time=round(meta_time*len)))
        
    
    prev_note,prev_len=seq[0],0
    for i in seq:
        if i!=-1:
            if prev_note==-1:
                raise RuntimeError("错误的输入格式 in seq2midi")
            playNote(prev_note,prev_len*cpn)
            prev_note,prev_len=i,1
        else:
            prev_len=prev_len+1
    
    if prev_note==-1:
        raise RuntimeError("错误的输入格式 in seq2midi")
    playNote(prev_note,prev_len*cpn)
    
    return mid

# play_midi_from_file: 从 file 中读取 MIDI 文件，并进行播放
def play_midi_from_file(file):
    print("playing music in",file)
    freq = 44100
    bitsize = -16
    channels = 2
    buffer = 1024
    pygame.mixer.init(freq, bitsize, channels, buffer)
    pygame.mixer.music.set_volume(1)
    clock = pygame.time.Clock()
    try:
        pygame.mixer.music.load(file)
    except:
        import traceback
        print(traceback.format_exc())
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        clock.tick(30)
        

# play_midi_from_mid: 直接从读取到 python 中(或者是自己编写)的 midi 文件播放
# 会将 midi 文件写入一个叫做 "TestMusic.midi" 的文件中，并且调用 play_midi_from_file
def play_midi_from_mid(mid):
    mid.save("TestMusic.midi")
    time.sleep(0.5)
    play_midi_from_file("TestMusic.midi")

if __name__ == "__main__":

    #seq = np.array([60,-1,62,-1,64,-1,65,-1,67,-1,65,-1,64,-1,62,-1,60,-1,64,-1,67,-1,64,-1,67,-1,-1,-1,67,-1,-1,-1])
    seq = np.array([57,59,60,62,64,-1,69,67,64,-1,57,-1,64,62,60,59,57,59,60,62,64,-1,62,60,59,57,59,60,59,57,56,59,
                    57,59,60,62,64,-1,69,67,64,-1,57,-1,64,62,60,59,57,59,60,62,64,-1,62,60,59,-1,60,-1,62,-1,64,-1,
                    57,59,60,62,64,-1,69,67,64,-1,57,-1,64,62,60,59,57,59,60,62,64,-1,62,60,59,57,59,60,59,57,56,59,
                    57,59,60,62,64,-1,69,67,64,-1,57,-1,64,62,60,59,57,59,60,62,64,-1,62,60,59,-1,60,-1,62,-1,64,-1,
                    67,69,64,62,64,-1,62,64,67,69,64,62,64,-1,62,64,62,60,59,55,57,-1,55,57,59,60,62,64,57,-1,64,67,
                    67,69,64,62,64,-1,62,64,67,69,64,62,64,-1,62,64,62,60,59,55,57,-1,55,57,59,60,62,64,57,-1,64,67,
                    67,69,64,62,64,-1,62,64,67,69,64,62,64,-1,62,64,62,60,59,55,57,-1,55,57,59,60,62,64,57,-1,64,67,
                    67,69,64,62,64,-1,62,64,67,69,64,62,64,-1,69,71,72,71,69,67,64,-1,62,64,62,60,59,55,57,-1,-1,-1])
    seq = seq + 6 # #F大调
    print(seq)
    # 这里的 seq 实现的是 bad apple!!!

    #mid = seq2midi(seq,npc=4)#
    mid = seq2midi(seq,npc=2,tempo=75)
    for i, track in enumerate(mid.tracks):
        print('Track {}: {}'.format(i, track.name))
        for msg in track:
            print(msg)
    
    play_midi_from_mid(mid)