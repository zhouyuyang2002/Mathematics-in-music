from os import remove
from datetime import datetime
import midi2seq as M2S
import seq2midi as S2M
import numpy as np
import random 
import math
import time
import mido
import os

# 手搓数据不易，且用且珍惜
seaLaugh = [78, -1, 78, 76, 73, -1, -1, 71, 69, -1, -1, -1, -1, -1, -1, -1,
            73, -1, -1, 71, 69, -1, 66, 64, 64, -1, -1, -1, -1, -1, -1, -1,
            64, -1, -1, 66, 64, -1, -1, 66, 69, -1, -1, 71, 73, -1, 76, -1,
            78, -1, -1, 76, 73, 71, 69, -1, 69, -1, -1, -1, -1, -1, -1, -1, 
            66, 69, 71, 73, 66, 69, 71, 73, 66, 69, 71, 73, 66, 69, 71, 73, 
            66, 69, 71, 73, 66, 69, 71, 73, 66, 69, 71, 73, 66, 69, 71, 73, 
            78, -1, 78, 76, 73, -1, 71, -1, 69, -1, -1, -1, -1, -1, -1, -1,
            73, 76, 73, 71, 69, -1, 66, -1, 64, -1, -1, -1, -1, -1, -1, -1]

# 全局的一个参考目标
ref = np.array([78, -1, 78, 76, 73, -1, -1, 71, 69, -1, -1, -1, -1, -1, -1, -1,
            73, -1, -1, 71, 69, -1, 66, 64, 64, -1, -1, -1, -1, -1, -1, -1,
            64, -1, -1, 66, 64, -1, -1, 66, 69, -1, -1, 71, 73, -1, 76, -1,
            78, -1, -1, 76, 73, 71, 69, -1, 69, -1, -1, -1, -1, -1, -1, -1, 
            66, 69, 71, 73, 66, 69, 71, 73, 66, 69, 71, 73, 66, 69, 71, 73, 
            66, 69, 71, 73, 66, 69, 71, 73, 66, 69, 71, 73, 66, 69, 71, 73, 
            78, -1, 78, 76, 73, -1, 71, -1, 69, -1, -1, -1, -1, -1, -1, -1,
            73, 76, 73, 71, 69, -1, 66, -1, 64, -1, -1, -1, -1, -1, -1, -1])
popN = 3000
threshold = 75
    
def mutate(pattern,score):
    random.seed(datetime.now())
    idx = -1
    seq = pattern
    
    def abs(x):
        if x < 0:
            return -x
        return x
    # 基于上一个音符 pre_note, 修改前的音符 note ,返回出一个随机音符
    def rand_note(pre_note,note):
        sum = 0.0
        prob_list = []
        for i in range(48 , 84+1):
            prob = 0
            prob = prob + 1.0/(0.1 * ((i-66) ** 2) + 1)
            prob = prob + 0.2/(0.4 * abs(i-note) + 3)
            prob = prob + 0.4/(0.4 * abs(i-pre_note) + 3)
            prob_list.append(prob)
            sum = sum + prob
        rp = random.uniform(0,1) * sum
        l = len(prob_list)
        for i in range(0, l):
            if rp <= (prob_list[i] + 1e-9):
                return i+48
            rp = rp - prob_list[i]
        return 84
    prev_note = 60
    for i in range(0, 128):
        if seq[i] != -1:
            c = random.uniform(0,1)
            if c < 0.10 * 40 / score: # 一个交换
                if idx >= 0: 
                    #print(idx, i)
                    seq[idx], seq[i] = seq[i], seq[idx]
                    idx = -1
                else:
                    idx = i
            elif c < 0.15 * 40 / score: # 换个音
                seq[i] = rand_note(prev_note,seq[i]);
            elif c < 0.20 * 40 / score: # 升或降8度 往中间凑
                if seq[i] > 72:
                    seq[i] = seq[i] - 12
                if seq[i] < 60:
                    seq[i] = seq[i] + 12
            prev_note = seq[i]
    # 得分越高，修改概率越低（希望能找到更好的乐谱）
    return seq


ratio = [0.35, 0.25, 0.30, 0.1]

def fit(seq):
    #规定一下目标的调调，看有多少个偏离的音，暂定C大调
    relative = [0, 2, 4, 5, 7, 9, 11]
    tone = []
    for i in range(48, 84, 12):
        for a in relative:
            tone.append(i + a)
    if 0 in relative:
        tone.append(84)

    # f0比较每个节内的平均音高
    # f1比较节内的音高方差 #感觉这个很迷，先不用看看
    # f2看有多少个不在给定调式音阶上的音 这三个指标是论文里的
    # f3相对音高序列相似度
    # f4节内平均音高的差异性，平方差的均值
    # f5离调音的比例
    # f6不和谐音程的比例
    f0, f1, f2, f3, f4, f5, f6 = 0, 0, 0, 0, 0, 0, 0
    
    for i in range(0, 128, 16): 
        note = []
        ref_note = []
        for j in range(i, i + 16):
            if seq[j] != -1:
                note.append(seq[j])
                if not (seq[j] in tone):
                    f2 = f2 + 1 
                    f5 = f5 + 1 
            if ref[j] != -1:
                ref_note.append(ref[j])
        f0 = f0 + abs(np.mean(note) - np.mean(ref_note))
        f1 = f1 + abs(np.var(note) - np.var(ref_note))
        f4 = f4 + (np.mean(note) - np.mean(ref_note)) ** 2
    
    def cal_f6():
        note = []
        for i in seq:
            if i != -1:
                note.append(i)
        l, sum0, sum1 = len(note), 0, 0
        good_pair = [-8, -7, -5, -4, -2, 2, 4, 5, 7, 8]
        for i in range(0, l-1):
            dif = note[i+1] - note[i]
            sum0 = sum0 + 1
            if dif in good_pair:
                sum1 = sum1 + 1
            if dif == 0:
               sum1 = sum1 - 1
        l = len(seq)
        for i in range(0, l-1):
            if seq[i] != -1:
                for j in range(1, 8):
                    if (i+j < l) and (seq[i+j] != -1):
                        dif = seq[i+j] - seq[i]
                        sum0 = sum0 + j ** (-1)
                        if dif in good_pair:
                            sum1 = sum1 + j ** (-1)
        return sum1 / sum0
    f6 = cal_f6() * 100;
    f0 = f0 / 8
    f1 = f1 / 8 # 对音节取平均
    f2 = 100.0 / (1 + f2) # 有多少个离调的音，认为离调的音越少越好
    f4 = math.exp(-f4) * 100
    # 感觉比较相对音高比较重要
    # 这里直接用点积求相似度看看效果
    mypitch = []
    refpitch = []
    length = 0
    for i in range(0, 128):
        if seq[i] != -1:
            mypitch.append(seq[i])
            refpitch.append(ref[i])
            length = length + 1
    f5 = 100.0 * (length - f5) / length
    for i in range(length - 1, 0, -1):
        mypitch[i] = mypitch[i] - mypitch[i - 1]
        refpitch[i] = refpitch[i] - refpitch[i - 1]
    f3 = 100 * 2.0 * np.dot(mypitch, refpitch) / (np.dot(mypitch, mypitch) + np.dot(refpitch, refpitch))

    
    #print(f0, f1, f2, f3, f4, f5)
    value = ratio[0] * f3 + ratio[1] * f4 + ratio[2] * f5 + ratio[3] * f6
    return value


def takeFit(ele): #算一个特定序列的值
    return ele[-1]

def generate(population):
    generation = population
    for k in range(0, 500): #迭代的最高轮次
        print("Round = ",k,np.array(generation).shape)
        pop_fit = []
        for x in generation: #保证每一代都有>= popN个人
            ele = list(x)
            pop_fit.append((ele, fit(ele)))
        pop_fit.sort(key=takeFit, reverse=True)
        
        if pop_fit[0][-1] > 60:
            mid = S2M.seq2midi(pop_fit[0][0], npc=2, tempo=75)
            for i, track in enumerate(mid.tracks):
                print('Track {}: {}'.format(i, track.name))
                for msg in track:
                    print(msg)
            S2M.play_midi_from_mid(mid)
            mid.save("TestMusic.midi")
        
        print(pop_fit[0][-1]) #看下这一代最优秀的有多秀
        print(pop_fit[1][-1]) #看下这一代最优秀的有多秀
        print(pop_fit[2][-1]) #看下这一代最优秀的有多秀
        print(pop_fit[3][-1]) #看下这一代最优秀的有多秀
        
        #if pop_fit[0][-1] > threshold:
        #    return list(pop_fit[0][0])
        
        generation = [] #保留前popN的人
        counter = 0
        for ele in pop_fit:
            generation.append(list(ele[0]))
            counter = counter + 1
            if counter == popN:
                break

        #开始变异
        #弄点无性繁殖，2k
        for i in range(0, 1000): 
            for j in range(0, 2):
                generation.append(mutate(list(pop_fit[i][0]),pop_fit[i][-1]))
                
        #在弄点有性繁殖, 1k个后代
        for l in range(0, 1000):
            i = random.randint(0, popN - 1)
            j = random.randint(0, popN - 1)
            if i != j:
                generation.append(list(pop_fit[i][0])[:64] + list(pop_fit[j][0])[64:])
            else:
                generation.append(mutate(list(pop_fit[i][0]),pop_fit[i][1])) 

        generation = list(set([tuple(x) for x in generation])) # 去重

    return 0

def rhythmAlign(seq):
    # 如果有效音不够，循环使用
    index = 0
    nseq = []
    for note in ref:
        if note == -1:
            nseq.append(-1)
        else:
            #找到下一个有效音
            idx = index
            while seq[index] == -1:
                index = (index + 1) % 128
                if index == idx:
                    break
            if (seq[index] == -1): #根本就没有有效音，拜拜
                return np.array([])
            nseq.append(seq[index])
            index = (index + 1) % 128
    return nseq

if __name__ == "__main__":
    #先听一下原版
    """   
    mid = S2M.seq2midi(seaLaugh, npc=2, tempo=75)
    for i, track in enumerate(mid.tracks):
        print('Track {}: {}'.format(i, track.name))
        for msg in track:
            print(msg)
    S2M.play_midi_from_mid(mid)
    time.sleep(5)
    """
    print(fit(seaLaugh))
    #注: 现在的情况是，MIDI里的东西过于nb, mutate过于拉垮，该用随机数据看看有没有长进
    '''
    # get seq data
    note_arr = np.load('Note_list.npdump', allow_pickle=True)
    note_arr = note_arr.tolist()

    # 先强行节奏对齐一下
    align_arr = []
    for ele in note_arr:
        align_ele = rhythmAlign(ele)
        if len(align_ele):
            align_arr.append(align_ele)
    print(np.array(align_arr).shape)
    '''
    # get random data
    align_arr = []
    for i in range(0, 5000):
        pitches = []
        for j in range(0, 128):
            pitches.append(random.randint(48, 84))
        align_arr.append(rhythmAlign(pitches))

    population = list(set([tuple(x) for x in align_arr])) # 去重

    generate(population[:popN])