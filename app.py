import io
import math
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title='SEC-HPLC Virtual Lab', page_icon='🧪', layout='wide')

DEFAULT = dict(stage='OFF', solvent=False, purged=False, column=False, equilibrated=False, blank=False, standard=False, sample=False, flow=0.5, salt=150, ph=7.0, temp=25, injection=10, pressure=0.0, logs=[], errors=0, faults=[], run_count=0, last_kind='', chromatogram=None, peaks=None, quiz={}, student='')
for k,v in DEFAULT.items():
    if k not in st.session_state:
        st.session_state[k] = v.copy() if isinstance(v,(list,dict)) else v
s=st.session_state

def log(msg, success=True):
    s.logs.append(('OK' if success else '주의',msg))
    if not success: s.errors += 1

def require(condition, message):
    if not condition:
        log(message,False)
        st.error(message)
        return False
    return True

def reset():
    for k,v in DEFAULT.items(): s[k]=v.copy() if isinstance(v,(list,dict)) else v

def pressure():
    # Arbitrary teaching model, NOT equipment pressure prediction
    return round((18 + 42*s.flow) * (1 + max(0,25-s.temp)*0.012) * (2.15 if '막힘' in s.faults else 1),1)

def make_trace(kind):
    t=np.linspace(0,18,901)
    rng=np.random.default_rng(17 + s.run_count)
    y=np.ones_like(t)*1.5
    peaks=[]
    if kind=='Blank':
        y+=rng.normal(0,0.28,len(t))
    else:
        # SEC: high-MW elutes before monomer, then LMW. Fixed elution order.
        comps=[('Aggregate',6.0,0.22,10),('Monomer',8.5,0.32,105),('LMW',11.4,0.26,5)]
        if kind=='Standard': comps=[('Monomer',8.5,0.32,105)]
        for name,mu,sigma,amp in comps:
            # Flow changes time but not chemical purity; conditions influence resolution only as pedagogical approximation.
            center=mu*(0.5/s.flow)
            width=sigma*(0.5/s.flow)*(1.6 if '분리 불량' in s.faults else 1)
            if kind=='Sample' and name=='Aggregate': amp=19
            if kind=='Sample' and name=='LMW': amp=7
            if '기포' in s.faults: amp*=0.8
            y+=amp*np.exp(-0.5*((t-center)/width)**2)
            area=amp*width*np.sqrt(2*np.pi)
            peaks.append({'성분':name,'RT (min)':round(center,2),'피크 면적 (모델값)':round(area,2),'폭 σ (min)':round(width,3)})
        y+=rng.normal(0,1.8 if '기포' in s.faults else 0.32,len(t))
    return pd.DataFrame({'Time (min)':t,'UV (mAU)':np.maximum(y,0)}),pd.DataFrame(peaks)

st.title('🧪 SEC-HPLC Virtual Lab')
st.caption('범용 HPLC · 3시간 교육 · 단백질 단량체/응집체 분석 · 가상 교육용 / 실제 장비 제어 불가')
with st.sidebar:
    st.text_input('학생/조 이름',key='student')
    page=st.radio('교육 메뉴',['① 장비 구조','② 장비 운용','③ 크로마토그램','④ 오류 대응','⑤ 평가·보고서'])
    st.divider()
    st.metric('장비 상태',s.stage)
    st.metric('가상 압력 (bar)',pressure() if s.stage!='OFF' else 0)
    st.metric('조작 오류 횟수',s.errors)
    if st.button('전체 실습 초기화',use_container_width=True):
        reset();st.rerun()

if page=='① 장비 구조':
    st.subheader('SEC-HPLC 구성요소와 흐름')
    st.info('이동상 저장병 → Degasser → Pump → Autosampler → SEC Column → UV Detector → Waste')
    cols=st.columns(3)
    elements=[('이동상 저장병','여과·탈기한 이동상을 공급합니다.'),('Degasser','이동상에 녹아 있는 기체를 줄입니다.'),('Pump','설정 유속으로 이동상을 이송합니다.'),('Autosampler','정해진 부피의 시료를 주입합니다.'),('SEC Column','수화역학적 크기에 따라 성분을 분리합니다.'),('UV Detector','용출 성분의 UV 흡광 신호를 측정합니다.')]
    for i,(name,desc) in enumerate(elements):
        with cols[i%3]:
            with st.container(border=True):
                st.markdown(f'**{i+1}. {name}**');st.write(desc)
    st.markdown('**용출 순서:** 고분자 응집체(HMW) → 단량체 → 저분자 성분(LMW). SEC에서는 큰 분자가 일반적으로 먼저 용출됩니다.')
    st.warning('실제 컬럼 연결 방향, 이동상 적합성, 허용 유속·압력, UV 설정, 시료 전처리는 제조사 SOP를 우선합니다.')
    st.divider()
    st.subheader('실제 장비·컬럼·연결부 사진으로 관찰하기')
    st.caption('아래 사진은 구성요소를 식별하기 위한 실제 HPLC 참조 사진입니다. 표시된 장비 모델과 교육 현장 장비는 다를 수 있으며, 조작·분해 지침으로 사용하면 안 됩니다.')
    reference_photos=[
        ('실제 HPLC 장비', 'https://commons.wikimedia.org/wiki/Special:FilePath/Hplc.JPG', '모듈 스택, 이동상 병, 유로 배치를 찾아보세요.', 'Kjaergaard / Wikimedia Commons · Public domain', 'https://commons.wikimedia.org/wiki/File:Hplc.JPG'),
        ('실제 HPLC 컬럼', 'https://commons.wikimedia.org/wiki/Special:FilePath/HPLC%20kolom.JPG', '컬럼 몸체, 라벨, 양 끝의 피팅 위치를 확인하세요.', 'Jmave, rcvanwijk / Wikimedia Commons · Public domain', 'https://commons.wikimedia.org/wiki/File:HPLC_kolom.JPG'),
        ('컬럼 및 유로 연결부', 'https://commons.wikimedia.org/wiki/Special:FilePath/Hplc%20column.JPG', '인젝터·튜빙·컬럼 연결의 위치를 관찰하세요. 피팅은 감압·SOP 확인 전 만지지 않습니다.', 'Kreecher / Wikimedia Commons · CC BY 4.0', 'https://commons.wikimedia.org/wiki/File:Hplc_column.JPG')
    ]
    photo_cols=st.columns(3)
    for col,(title,url,guide,credit,source) in zip(photo_cols,reference_photos):
        with col:
            st.image(url,caption=title,use_container_width=True)
            st.write(guide)
            st.caption(credit)
            st.markdown(f'[원본·라이선스 확인]({source})')
    st.subheader('우리 실험실 장비 사진')
    st.write('교육 담당자는 현장 장비 사진을 올려 모델별 모듈명·컬럼 방향·튜빙 경로를 함께 설명할 수 있습니다. 업로드한 파일은 이번 브라우저 세션에서만 표시됩니다.')
    local_photos=st.file_uploader('현장 사진 업로드 (장비 전체 / 컬럼 / 연결부)',type=['png','jpg','jpeg'],accept_multiple_files=True,help='압력 표시, 시리얼 번호, 개인 정보 등 민감한 정보가 보이지 않는 사진만 사용하세요.')
    if local_photos:
        local_cols=st.columns(min(3,len(local_photos)))
        for i,photo in enumerate(local_photos):
            with local_cols[i%len(local_cols)]:
                st.image(photo,caption=f'현장 사진: {photo.name}',use_container_width=True)
    with st.expander('사진 관찰 체크리스트'):
        st.markdown('''
        - 이동상 병에서 펌프, 주입부, 컬럼, 검출기, 폐액으로 이어지는 유로를 손가락으로 따라가 보세요.
        - 컬럼의 유입/유출 방향 화살표와 현장 SOP의 방향이 일치하는지 **강사와 함께** 확인하세요.
        - 튜빙의 꺾임·누액·기포 징후는 관찰만 하고, 실제 조치는 장비 전원을 안전하게 정지한 뒤 SOP에 따르세요.
        ''')

elif page=='② 장비 운용':
    st.subheader('가상 운용 콘솔')
    a,b,c=st.columns(3)
    with a:
        s.flow=st.slider('유속 (mL/min)',0.1,1.0,float(s.flow),0.1)
        s.salt=st.slider('완충액 염 농도 (mM)',0,300,int(s.salt),25)
    with b:
        s.ph=st.slider('이동상 pH',5.0,8.5,float(s.ph),0.1)
        s.temp=st.slider('컬럼 온도 (°C)',15,40,int(s.temp),1)
    with c:
        s.injection=st.slider('주입량 (µL)',1,50,int(s.injection),1)
        st.metric('모의 시스템 압력',f'{pressure() if s.stage!="OFF" else 0} bar')
    st.caption('압력은 조작 연습을 위한 임의 모델값이며 실제 장비·컬럼의 압력 계산에 사용할 수 없습니다. 설정값 역시 교육용 예시입니다.')
    if pressure()>100 and s.stage!='OFF': st.error('가상 고압 경고: 운용을 중단하고 막힘 여부를 확인하세요.')
    x,y,z=st.columns(3)
    with x:
        if st.button('1. 이동상 확인',use_container_width=True):
            s.solvent=True;log('이동상 확인 완료')
        if st.button('2. 전원 켜기',use_container_width=True):
            if require(s.solvent,'먼저 이동상 및 폐액 용기를 확인하세요.'):
                s.stage='READY';log('전원 ON')
        if st.button('3. Purge',use_container_width=True):
            if require(s.stage=='READY','Purge 전 장비 준비 상태를 확인하세요.'):
                s.purged=True;log('가상 Purge 완료')
    with y:
        if st.button('4. 컬럼 연결 확인',use_container_width=True):
            if require(s.purged,'컬럼 연결 전 유로 준비와 Purge를 완료하세요.'):
                s.column=True;log('컬럼 연결 확인')
        if st.button('5. Pump ON / 평형화',use_container_width=True):
            if require(s.column and s.stage=='READY','컬럼 연결 및 READY 상태가 필요합니다.') and require(pressure()<=100,'가상 고압 경고: Pump를 가동할 수 없습니다.'):
                s.equilibrated=True;s.stage='EQUILIBRATED';log('가상 평형화 완료')
        if st.button('6. Pump STOP',use_container_width=True):
            if s.stage!='OFF': s.stage='READY';s.equilibrated=False;log('Pump STOP')
    with z:
        for kind in ['Blank','Standard','Sample']:
            if st.button(f'{kind} 주입 및 Run',use_container_width=True):
                good=s.stage=='EQUILIBRATED' and pressure()<=100
                if kind=='Standard': good=good and s.blank
                if kind=='Sample': good=good and s.standard
                if require(good,'평형화와 분석 순서(Blank → Standard → Sample)를 확인하세요.'):
                    s.run_count+=1;s.chromatogram,s.peaks=make_trace(kind);s.last_kind=kind
                    if kind=='Blank':s.blank=True
                    if kind=='Standard':s.standard=True
                    if kind=='Sample':s.sample=True
                    log(f'{kind} 분석 완료');st.success(f'{kind} 분석 완료. ③ 결과 화면에서 확인하세요.')
        if st.button('세척·종료',use_container_width=True):
            if require(s.stage!='OFF','장비가 꺼져 있습니다.'):
                s.stage='OFF';s.equilibrated=False;log('가상 세척·종료 완료 (실제 세척 SOP와 별개)')
    st.subheader('실습 이벤트 기록')
    if s.logs:st.dataframe(pd.DataFrame(s.logs,columns=['상태','이벤트']),use_container_width=True,hide_index=True)
    else:st.write('아직 기록이 없습니다.')

elif page=='③ 크로마토그램':
    st.subheader('SEC-UV 크로마토그램')
    if s.chromatogram is None:
        st.info('② 장비 운용에서 Blank → Standard → Sample을 순서대로 분석하세요.')
    else:
        st.write(f'최근 분석: **{s.last_kind}**')
        st.line_chart(s.chromatogram.set_index('Time (min)'),height=320)
        st.download_button('크로마토그램 CSV 저장',s.chromatogram.to_csv(index=False).encode('utf-8-sig'),'sec_hplc_trace.csv','text/csv')
        if s.peaks is not None and not s.peaks.empty:
            p=s.peaks.copy();total=p['피크 면적 (모델값)'].sum();p['면적 비율 (%)']=(p['피크 면적 (모델값)']/total*100).round(2)
            st.dataframe(p,use_container_width=True,hide_index=True)
            mon=p.loc[p['성분']=='Monomer','면적 비율 (%)']
            agg=p.loc[p['성분']=='Aggregate','면적 비율 (%)']
            c1,c2=st.columns(2)
            c1.metric('단량체 UV 면적 비율',f'{mon.iloc[0]:.2f}%' if len(mon) else 'N/A')
            c2.metric('응집체 UV 면적 비율',f'{agg.iloc[0]:.2f}%' if len(agg) else 'N/A')
            st.download_button('피크 분석 CSV 저장',p.to_csv(index=False).encode('utf-8-sig'),'sec_hplc_peaks.csv','text/csv')
        st.caption('피크는 가정된 Gaussian 신호로 생성됩니다. 피크 면적은 모델에서 계산한 값이며 실제 자동 적분 결과가 아닙니다. UV 면적 비율은 검증 없이 질량 순도와 동일시할 수 없습니다.')

elif page=='④ 오류 대응':
    st.subheader('장비 이상 상황 대응')
    fault=st.selectbox('가상 이상 상황 선택',['막힘','기포','분리 불량'])
    if st.button('이상 상황 발생'):
        if fault not in s.faults:s.faults.append(fault)
        log(f'{fault} 상황 발생');st.warning(f'{fault} 상황이 활성화되었습니다.')
    st.write('현재 활성 이상:',', '.join(s.faults) if s.faults else '없음')
    choices={'막힘':['유속을 높여 압력을 극복한다','펌프를 중단하고 유로·필터·컬럼을 SOP에 따라 점검한다','경고를 무시한다'], '기포':['Degasser와 Purge 절차를 점검한다','검출기 파장을 임의 변경한다','주입량을 늘린다'], '분리 불량':['컬럼·유속·시료량·이동상 적합성을 점검한다','피크를 수동 삭제한다','압력 제한을 해제한다']}
    ans=st.radio('적절한 조치는?',choices[fault],index=None)
    correct={'막힘':choices['막힘'][1],'기포':choices['기포'][0],'분리 불량':choices['분리 불량'][0]}
    if st.button('조치 실행'):
        if ans==correct[fault]:
            if fault in s.faults:s.faults.remove(fault)
            log(f'{fault} 문제 해결');st.success('적절한 대응입니다. 가상 이상이 해제되었습니다.')
        else:
            log('부적절한 오류 대응',False);st.error('안전하거나 적절한 조치가 아닙니다. 다시 선택하세요.')
    st.caption('실제 장비에서는 이상 발생 시 실험실 SOP와 제조사 지침을 따르고, 승인 없는 분해·압력 변경은 금지합니다.')

else:
    st.subheader('최종 평가 및 결과 보고')
    questions=[('SEC에서 일반적으로 먼저 용출되는 것은?',['단량체','큰 응집체','작은 분해물'],1),('시료 분석 전 일반적으로 확인할 것은?',['평형화와 Blank/Standard','결과 삭제','유속 최대로 변경'],0),('UV 면적비를 질량 순도로 바로 단정해도 될까요?',['예','아니오'],1),('가상 압력이 급증하면?',['펌프 중단 및 점검','유속 증가','경고 무시'],0),('Purge의 주요 목적은?',['유로 내 기포 제거','단백질 정량','컬럼 충전'],0)]
    for i,(q,opts,correct) in enumerate(questions):
        s.quiz[str(i)]=st.radio(f'Q{i+1}. {q}',opts,index=None,key=f'quiz_{i}')
    score=sum(20 for i,(_,opts,correct) in enumerate(questions) if s.quiz.get(str(i))==opts[correct])
    if st.button('채점하기'):st.success(f'퀴즈 점수: {score}/100점')
    completed=sum([s.blank,s.standard,s.sample]);st.metric('운용 단계 완료',f'{completed}/3')
    report=f'''SEC-HPLC Virtual Lab 실습 보고서\n학생/조: {s.student or "미입력"}\n장비: 범용 가상 HPLC\n운용 완료: Blank={s.blank}, Standard={s.standard}, Sample={s.sample}\n퀴즈 점수: {score}/100\n조작 오류 횟수: {s.errors}\n최근 분석: {s.last_kind}\n유속: {s.flow} mL/min, 이동상 pH: {s.ph}, 염 농도: {s.salt} mM\n주의: 모든 수치는 교육용 가상 모델 결과이며 실제 분석 데이터가 아닙니다.\n\n실습 로그:\n'''+ '\n'.join(f'{status}: {msg}' for status,msg in s.logs)
    st.download_button('실습 보고서 TXT 다운로드',report.encode('utf-8-sig'),'SEC_HPLC_Student_Report.txt','text/plain')
