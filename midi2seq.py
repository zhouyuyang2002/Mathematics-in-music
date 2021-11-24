import numpy as np
import pygame
import time
import mido
import os

# 数据集来源于 https://github.com/jukedeck/nottingham-dataset，这里只选取了 Track 0 对其进行编号
# MIDI 文件中不包含 BPM 值，因而统一采用了 256ms 作为一个十六音符的时长。
# 部分乐曲中包含了三连音等非十六分音符的整数倍时值的音，这些乐谱不会进入统计数据。
# 部分乐曲拍号为 3/4 或 6/8，数据处理的时候忽略了拍号的影响，统一按照 Note 序列进行处理。强度的信息也被忽略。
# 最后选取了相邻的 128 个 Note 进行比较，采样方式为每隔16个采样一次，采样区间如果分割了乐音会进行修正，保证每个 NoteList 第一个数字不是 -1



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

def get_midi():
    dir=os.getcwd()
    dir=dir+"/MIDI"
    dir_list=[]
    for file in os.listdir(dir):
        if file[-4:]=='.mid':
            dir_list.append('MIDI/'+file)
    return dir_list

def Read_midi(dir):
    print("Reading MIDI File",dir)
    mid=mido.MidiFile(dir)
    track=mid.tracks[0]
    note_list=[]
    note=1
    for msg in track:
        #print(msg)
        if msg.type == 'note_on':
            note=msg.note
        elif msg.type == 'note_off':
            # 假设一个 16 分音符的时值为 256ms
            time=int((msg.time+255)/256)
            # 如果出现了不是十六分音符的音符，则会整条删除
            # 暂时不考虑空拍子的情况
            if time*256!=msg.time:
                print("Bad message:",msg)
                return [],1;
            note_list.append(note)
            for i in range(1,time):
                note_list.append(-1)
    return note_list,0
    

if __name__ == "__main__":
    dir_list=get_midi()
    note_arr=[]
    for dir in dir_list:
        note_list,bad_flag=Read_midi(dir)
        if bad_flag==0:
            l=len(note_list)
            # 每一段长度8小节，包含128个note，编码方式同 README
            fir_note,fir_id=-1,-1
            for i in range(0,l-128,16):
                for j in range(fir_id+1,i+1):
                    if note_list[j]!=-1:
                        fir_note=note_list[j]
                note_list[i]=fir_note
                note_arr.append(np.array(note_list[i:i+128]))
                fir_id=i
    note_arr=np.array(note_arr)
    print(note_arr.shape)
    print(note_arr[4117])
    play_midi_from_mid(note_arr[4117])
    note_arr.dump("Note_list.npdump")