# -*- coding: utf-8 -*-
"""
Created on Thu Oct  9 13:28:53 2025

@author: dr636
"""

import os, sys
import requests
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen
import urllib.request
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np


# %%Import Jesse's LC.
directory_name='F:/Consulting/Urban Institute/'
os.chdir(directory_name)

lc_df=pd.read_csv('DIGITIZED-LEGAL-COMPENDIUM-V2019.csv',encoding='latin-1')

#Create df for matched statutes.
current_df=lc_df.loc[lc_df.backsources_2019==lc_df.backsources_2023]
current_df=current_df.loc[((current_df.backsources_2019.isnull()==False) & (pd.isnull(current_df.backsources_2023)==False))]
current_df=current_df.loc[((current_df.backsources_2023!='No') & (current_df.backsources_2023!='NO'))]

#Manual entry of multi issue.
current_df.loc[102,'MULTI']='CHECK §§'
current_df.loc[927,'MULTI']='CHECK §§'

#Create multi dataframe.
multi_df=current_df.loc[current_df['MULTI']=='CHECK §§']

#Remove states done manually.
multi_df=multi_df.loc[~multi_df.state.isin(['Delaware','Kentucky','North Dakota'])]
multi_df=multi_df[['state','backsources_2023']].reset_index()

#Load main_df.
main_df=pd.read_csv('current_text_v1.csv')

#Load temp_df.
if os.path.isfile('multi_text_v1.csv'):
    temp_df=pd.read_csv('multi_text_v1.csv')
else:
    temp_df=pd.DataFrame()

#Set up request.
user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'


# %%Arkansas.
temp=pd.DataFrame(columns=['index','state','title','subtitle','chapter','subchapter','section','section_url','url'])
for i in range(401,417):
    temp.loc[i-401]=[102,'arkansas','4','3','28','4',f'{i}','4-28-'+f'{i}','https://law.justia.com/codes/arkansas/2023/title-4/subtitle-3/chapter-28/subchapter-4/'+'section-4-28-'+f'{i}/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section_url'])==False:
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        #text=soup.find('div',id='codes-content')
        mod_text=soup.find_all('em')
        if mod_text is None:
            mod_text=''
        else:
            for j in mod_text:
                temp.loc[i,'statute_mods']=temp.loc[i,'statute_mods']+j.get_text()
        
        text=soup.find('div',id='codes-content').prettify().split('<em>')[0]
        def remove_html_tags_regex(text):
            clean = re.compile('<.*?>')
            return re.sub(clean,'', text).replace('\n','').replace("  ","")

        temp.loc[i,'statute_text']=remove_html_tags_regex(text)
        #temp.loc[i,'statute_mods']=''.join(mod_text)
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=temp.copy()
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Idaho.
temp=pd.DataFrame(columns=['index','state','title','chapter','section','section_url','url'])
for i in range(1501,1513):
    temp.loc[i-1501]=[683,'idaho','48','15',f'{i}','48-'+f'{i}','https://law.justia.com/codes/idaho/2023/title-48/chapter-15/section-48-'+f'{i}/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')        
        text=text.get_text().split('History:')
        temp.loc[i,'statute_text']=''.join(text[0])
        if len(text)==2:
            temp.loc[i,'statute_mods']=''.join(text[1])
        else:
            temp.loc[i,'statute_mods']=''
            
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Kansas.
temp=pd.DataFrame(columns=['index','state','chapter','article','section','section_url','url'])
for i in range(1759,1777):
    temp.loc[i-1759]=[848,'kansas','17','17',f'{i}','17-'+f'{i}','https://law.justia.com/codes/kansas/2023/chapter-17/article-17/section-17-'+f'{i}/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'url'])==False:
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text().split('History:')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']='History:'+''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)


# %%Louisiana.
temp=pd.DataFrame(columns=['index','state','title','section','section_url','url'])
for i in range(11,24):
    temp.loc[i-11]=[927,'louisiana','40',f'{i}','rs-40-2115-'+f'{i}','https://law.justia.com/codes/louisiana/2023/revised-statutes/title-40/rs-40-2115-'+f'{i}/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section'])==False:
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        #text=text.get_text(separator='em', strip=True).split('em')
        if url=='https://regulations.justia.com/states/louisiana/title-16/part-iii/chapter-5/section-iii-515/':
            text=soup.find_all('div',class_='content-indent')
            content_text=[]
            for j in text:
                content_text.append(j.get_text())
            text=''.join(content_text)
            temp.loc[i,'statute_text']=text.replace('\t', '').replace('\n','')
            
            mod_text=soup.find_all('p')
            for j in mod_text:
                if j.get_text().find('AUTHORITY NOTE:')!=-1:
                    mod_content_text=j.get_text()
               
            temp.loc[i,'statute_mods']=mod_content_text.replace('\t', '').replace('\n','')
            
            #This gets the universal citation.
            temp.loc[i,'universal_citation']=soup.find('div',class_='has-margin-bottom-20').get_text()
        else:
            text=soup.find('div',id='codes-content')
            text=text.get_text(separator='</p> <p>', strip=True).split('</p> <p>Acts')
            text[0]=text[0].replace('</p> <p>','')
            temp.loc[i,'statute_text']=''.join(text[0])
            temp.loc[i,'statute_mods']='Acts '+''.join(text[1])
            
            #This gets the universal citation.
            temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Massachusetts.
temp=pd.DataFrame(columns=['index','state','part','title','chapter','section','section_url','url'])
temp.loc[0]=[992,'massachusetts','i','xi','68','19','19','https://law.justia.com/codes/massachusetts/part-i/title-xi/chapter-68/section-19/']
temp.loc[1]=[992,'massachusetts','i','xi','68','19a','19a','https://law.justia.com/codes/massachusetts/part-i/title-xi/chapter-68/section-19a/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if temp.loc[i,'chapter']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text()
        temp.loc[i,'statute_text']=''.join(text)
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Maryland.
temp=pd.DataFrame(columns=['index','state','title','subtitle','section','section_url','url'])
section_list_1=['101','102']
section_list_2=['201','202','203','204','205']

for i in range(0,len(section_list_1)):
    temp.loc[i]=[1004,'maryland','6','1',section_list_1[i],'6-'+section_list_1[i],'https://law.justia.com/codes/maryland/2023/business-regulation/title-6/subtitle-1/section-6-'+section_list_1[i]+'/']

for i in range(0,len(section_list_2)):
    temp.loc[i+3]=[1004,'maryland','6','2',section_list_2[i],'6-'+section_list_2[i],'https://law.justia.com/codes/maryland/2023/business-regulation/title-6/subtitle-2/section-6-'+section_list_2[i]+'/']

temp.loc[8]=[1004,'maryland','6','4','401','6-401','https://law.justia.com/codes/maryland/2023/business-regulation/title-6/subtitle-4/section-6-401/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section'])==False:
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text()
        temp.loc[i,'statute_text']=''.join(text)
        #temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Maine.
temp=pd.DataFrame(columns=['index','state','title','part','chapter','section','section_url','url'])
section_list=['5001','5002','5003','5004','5005','5005-a','5005-b','5006','5007','5008','5008-a','5008-b','5009','5010','5011','5011-a','5012','5012-a','5013','5014','5015','5015-a','5016','5017','5018']

for i in range(0,len(section_list)):
    temp.loc[i]=[1057,'maine','9','13','385',section_list[i],'48-'+section_list[i],'https://law.justia.com/codes/maine/2023/title-9/part-13/chapter-385/section-'+section_list[i]+'/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'url'])==False:
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        #text=text.get_text(separator='em', strip=True).split('em')
        text=text.get_text().split('SECTION HISTORY')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Mississippi.
temp=pd.DataFrame(columns=['index','state','title','chapter','section','paragraph','section_url','section_name','url'])
section_list=['501','503','504','505','507','509','511','513','515','517','518','519','521','523','524','525','526','527','529']

for i in range(0,len(section_list)):
    temp.loc[i]=[1254,'mississippi','79','11',section_list[i],'','79-11-'+section_list[i],'regulation-of-charitable-solicitations','https://law.justia.com/codes/mississippi/2023/title-79/chapter-11/regulation-of-charitable-solicitations/section-79-11-'+section_list[i]+'/']
    
temp.loc[i+1]=[1270,'mississippi','79','11','504','(a)','79-11-504','regulation-of-charitable-solicitations','https://law.justia.com/codes/mississippi/2023/title-79/chapter-11/regulation-of-charitable-solicitations/section-79-11-504/']
temp.loc[i+2]=[1270,'mississippi','79','11','515','','79-11-515','regulation-of-charitable-solicitations','https://law.justia.com/codes/mississippi/2023/title-79/chapter-11/regulation-of-charitable-solicitations/section-79-11-515/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    #Temporary if condition.
    if temp.loc[i,'section']!='5':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        mod_text=soup.find('em')
        if mod_text is None:
            mod_text=''
        else:
            mod_text=mod_text.get_text()

        text=text.get_text().split('Laws,')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(mod_text)
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()


#Manually update statutes.
temp.loc[19,'statute_text']='(a) Promulgate rules of procedure and regulations necessary for the administration of Sections 79-11-501 through 79-11-529, Mississippi Code of 1972, subject to the provisions of the Mississippi Administrative Procedures Law.'
temp.loc[21]=[1270,'mississippi','','','','','','','https://www.law.cornell.edu/regulations/mississippi/1-Miss-Code-R-SS-15-3-17','(A) A Commercial Co-venturer engaging in a charitable sales promotion is required to file with the Secretary of State an online notice of the promotion no less than seven (7) days prior to the start of said promotion. Such notice must include a copy of the contract between the Co-venturer and the Charitable Organization. (B) The Secretary of State also requires a Commercial Co-venturer to file an online financial accounting of the charitable sales promotion no later than thirty (30) days after the conclusion of said promotion, if the charitable sales promotion is less than one (1) year. If the promotion period is greater than one (1) year, the Commercial Co-Venture shall file an annual online financial accounting each year of the charitable sales promotion no later than thirty (30) days after the anniversary date of the first notice of promotion filing, and shall file a final financial accounting of the charitable sales promotion no later than thirty (30) days after the conclusion of said promotion. The online accounting, annual accounting or final accounting shall include the following: (1) The number of units of goods or services sold in Mississippi; (2) The amount of gross sales in Mississippi; (3) The amount of those gross sales paid by the Co-venturer to the Charitable Organization; and (4) In the case of a multi-state, national or international campaign, the percentage of total sales in Mississippi paid to the charity. (C) It shall be a violation of the Mississippi Regulation of Charitable Solicitations Act for a Commercial Co-venturer to perform any services on behalf of an unregistered charitable organization.','Amended 11/1/2015 Amended 4/7/2017 Amended 12/20/2017 Amended 8/25/2022','1 Miss. Code. R. 15-3.17']

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)


# %%Montana.
temp=pd.DataFrame(columns=['index','state','title','chapter','part','section','section_url','url'])

for i in range(701,720):
    if i==706:
        continue
    temp.loc[i-701]=[1325,'montana','50','4','7',f'{i}','50-4-'+f'{i}','https://law.justia.com/codes/montana/2023/title-50/chapter-4/part-7/section-50-4-'+f'{i}/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('History:')
        temp.loc[i,'statute_text']=''.join(text[0])
        if temp.loc[i,'section']=='705':
            temp.loc[i,'statute_mods']=''
        else:
            temp.loc[i,'statute_mods']='History:'+''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)


# %%North Carolina. Pull from main_df, 131 already matched with correct index.
temp=main_df.loc[main_df['index'].isin([1372,1373]),['index','state','title','chapter','section','subsection','paragraph','section_url','article','url','statute_text','statute_mods','universal_citation']]
temp['index']=1374
temp.loc[temp['index']==1374,['state','statute_text']]=['north carolina','']

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Nebraska. Neb. Rev. Stat. §§ 71-20,102 - 71-20,114.
temp=pd.DataFrame(columns=['index','state','title','chapter','section','section_url','url'])
for i in range(102,115):
    temp.loc[i-102]=[1470,'nebraska','','71',f'{i}','71-20-'+f'{i}','https://law.justia.com/codes/nebraska/2023/chapter-71/statute-71-20-'+f'{i}/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=text.get_text().split('Source')
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(text[1])
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%New York.
temp=pd.DataFrame(columns=['index','state','section','paragraph','section_url','article','part','law_name','url','statute_text','statute_mods','universal_citation'])

#Manual statutes.
index_list=[1724,1725]
j=0
for i in range(0,len(index_list)):
    temp.loc[i+j]=[index_list[i],'new york','172-a','(2)(a)','172-a','7-a','','exc','https://law.justia.com/codes/new-york/2023/exc/article-7-a/172-a/','(a) An educational institution confining its solicitation of contributions to its student body, alumni, faculty and trustees, and their families.','','NY Exec L § 172-A (2023)']
    temp.loc[i+j+1]=[index_list[i],'new york','172-a','(2)(g)','172-a','7-a','','exc','https://law.justia.com/codes/new-york/2023/exc/article-7-a/172-a/','(g) An educational institution which files annual financial reports with the regents of the university of the state of New York as required by the education law or with an agency having similar jurisdiction in another state or a library which files annual financial reports as required by the state education department.','','NY Exec L § 172-A (2023)']
    temp.loc[i+j+2]=[index_list[i],'new york','8-1.4','(b)(4)','8-1-4','8','1','ept','https://law.justia.com/codes/new-york/2023/ept/article-8/part-1/8-1-4/','(4) educational institutions incorporated under the education law or by special act','','NY Est Pow & Trusts L § 8-1.4 (2023)']
    j=2
temp_df=pd.concat([temp_df,temp],ignore_index=True)

#Reset temp.
temp=pd.DataFrame(columns=['index','state','section','paragraph','section_url','article','part','law_name','url','statute_text','statute_mods','universal_citation'])
j=0
for i in [1745,1746,1747]:
    temp.loc[j]=[i,'new york','112','(a)(4)','112','1','','npc','https://law.justia.com/codes/new-york/2023/npc/article-1/112/','(4) To procure a judgment removing a director of a corporation for cause under section 706 (Removal of directors);','','NY Not for Profit Corp L § 112 (2023)']
    j+=1
temp_df=pd.concat([temp_df,temp],ignore_index=True)

#Reset temp.
temp=pd.DataFrame(columns=['index','state','section','paragraph','section_url','article','part','law_name','url','statute_text','statute_mods','universal_citation'])
j=0
for i in [1748,1749]:
    temp.loc[j]=[i,'new york','112','(a)(5)','112','1','','npc','https://law.justia.com/codes/new-york/2023/npc/article-1/112/','(5) To dissolve a corporation under article 11 (Judicial dissolution);','','NY Not for Profit Corp L § 112 (2023)']
    j+=1
temp_df=pd.concat([temp_df,temp],ignore_index=True)

#Reset temp.
temp=pd.DataFrame(columns=['index','state','section','paragraph','section_url','article','part','law_name','url','statute_text','statute_mods','universal_citation'])
j=0
for i in [1745,1746,1747,1748,1749]:
    temp.loc[j]=[i,'new york','63','(15)','63','5','','exc','https://law.justia.com/codes/new-york/2023/exc/article-5/63/','15. In any case where the attorney general has authority to institute a civil action or proceeding in connection with the enforcement of a law of this state, in lieu thereof he may accept an assurance of discontinuance of any act or practice in violation of such law from any person engaged or who has engaged in such act or practice. Such assurance may include a stipulation for the voluntary payment by the alleged violator of the reasonable costs and disbursements incurred by the attorney general during the course of his investigation. Evidence of a violation of such assurance shall constitute prima facie proof of violation of the applicable law in any civil action or proceeding thereafter commenced by the attorney general.','','NY Exec L § 63 (2023)']
    j+=1

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

#Automated statutes.
temp=pd.DataFrame(columns=['index','state','section','paragraph','section_url','article','part','law_name','url','statute_text','statute_mods','universal_citation'])

section_list=['171-a','172','172-a','172-b','172-c','172-d','172-e','172-f','173','173-a','173-b','173-c','174','174-a','174-b','174-c','174-d','175','175-a','175-b','176','177']

k=0
for j in [1743,1744]:
    for i in range(0,len(section_list)):
        temp.loc[i+k*len(section_list)]=[j,'new york',section_list[i],'',section_list[i],'7-a','','exc','https://law.justia.com/codes/new-york/2023/exc/article-7-a/'+section_list[i]+'/','','','']
    k=1
temp.loc[44]=[1743,'new york','8-1.4','','8-1-4','8','1','ept','https://law.justia.com/codes/new-york/2023/ept/article-8/part-1/8-1-4/','','','']
temp.loc[45]=[1744,'new york','8-1.4','','8-1-4','8','1','ept','https://law.justia.com/codes/new-york/2023/ept/article-8/part-1/8-1-4/','','','']

temp.loc[46]=[1748,'new york','1101','','1101','11','','npc','https://law.justia.com/codes/new-york/2023/npc/article-11/1101/','','','']
temp.loc[47]=[1749,'new york','1101','','1101','11','','npc','https://law.justia.com/codes/new-york/2023/npc/article-11/1101/','','','']

j=0
for i in [1745,1746,1747]:
    temp.loc[j+48]=[i,'new york','706','','706','7','','npc','https://law.justia.com/codes/new-york/2023/npc/article-7/706/','','','']
    temp.loc[j+51]=[i,'new york','175','','175','7-a','','exc','https://law.justia.com/codes/new-york/2023/exc/article-7-a/175/','','','']
    j+=1

section_list=['510','511','511-a']
k=0
for j in [1753,1754,1755]:
    for i in range(0,len(section_list)):
        k+=1
        temp.loc[k+54]=[j,'new york',section_list[i],'',section_list[i],'5','','npc','https://law.justia.com/codes/new-york/2023/npc/article-5/'+section_list[i]+'/','','','']

temp.loc[64]=[1753,'new york','12','','12','2','','rco','https://law.justia.com/codes/new-york/2023/rco/article-2/12/','','','']
temp.loc[65]=[1754,'new york','12','','12','2','','rco','https://law.justia.com/codes/new-york/2023/rco/article-2/12/','','','']

#Get statute text.
for i in temp.index:
    url=temp.loc[i,'url']
    print(f"Fetching: {url}")
    req=urllib.request.Request(url,headers={'User-Agent': user_agent,})
    page = urlopen(req)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    soup.find('div',id='codes-content').get_text()

    #This separates text into statute and previous amendments to statute.
    text=soup.find('div',id='codes-content')
    text=text.get_text()
    temp.loc[i,'statute_text']=''.join(text)
    temp.loc[i,'statute_mods']=''
    
    #This gets the universal citation.
    temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)


# %%Oregon.
temp=pd.DataFrame(columns=['index','state','volume','chapter','section','section_url','url'])
j=0
for i in [800,803,805,807,809,811,813,815]:
    temp.loc[j]=[1890,'oregon','2','065',f'{i}','65-'+f'{i}','https://law.justia.com/codes/oregon/volume-02/chapter-065/section-65-'+f'{i}/']
    j+=1

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section_url'])==False:
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req=urllib.request.Request(url,headers={'User-Agent': user_agent,})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        text=re.split(r'(\[\d+)',text.get_text())
        temp.loc[i,'statute_text']=''.join(text[0])
        temp.loc[i,'statute_mods']=''.join(text[1:])
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Tennessee.
temp=pd.DataFrame(columns=['index','state','title','chapter','part','section','section_url','url'])
for i in range(201,212):
    temp.loc[i-201]=[2142,'tennessee','48','68','2',f'{i}','48-68-'+f'{i}','https://law.justia.com/codes/tennessee/2023/title-48/nonprofit-corporations/chapter-68/part-2/section-48-68-'+f'{i}/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    print(f"Fetching: {url}")
    url=temp.loc[i,'url']
    req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
    page = urlopen(req)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    content_div=soup.find('div',id='codes-content')
    text_content=content_div.get_text()
    # Split at amendment indicators common on TN pages
    patterns=[r'History', r'Amended by', r'Acts\s+\d{4}', r'Compiler\'s Notes']
    split_pos=len(text_content)
    for pat in patterns:
        m=re.search(pat, text_content)
        if m and m.start()<split_pos:
            split_pos=m.start()
    statute_text=text_content[:split_pos].strip()
    statute_mods=text_content[split_pos:].strip() if split_pos<len(text_content) else ''
    temp.loc[i,'statute_text']=statute_text
    temp.loc[i,'statute_mods']=statute_mods

    cit_div=soup.find('div', class_='citation')
    if cit_div and cit_div.find('span'):
        temp.loc[i,'universal_citation']=cit_div.find('span').get_text()
    else:
        temp.loc[i,'universal_citation']=''

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Utah.
temp=pd.DataFrame(columns=['index','state','title','chapter','rule','section','section_url','url'])
for i in range(1,24):
    if i==7 or i==10 or i==20:
        continue
    temp.loc[i-1]=[2226,'utah','13','22','',f'{i}',f'{i}','https://law.justia.com/codes/utah/2023/title-13/chapter-22/section-'+f'{i}/']

for i in range(1,10):
    temp.loc[i+22]=[2226,'utah','r152','','r152-22',f'{i}','r152-22-'+f'{i}','https://regulations.justia.com/states/utah/commerce/title-r152/rule-r152-22/section-r152-22-'+f'{i}/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if pd.isnull(temp.loc[i,'section_url'])==False:
        try:
            url=temp.loc[i,'url']
            print(f"Fetching: {url}")
            req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
            page = urlopen(req)
            html = page.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            
            # Get the main content
            content_div = soup.find('div', id='codes-content')
            if content_div:
                text_content = content_div.get_text()
                
                # Extract statute text and modifications using regex
                # Look for common amendment patterns in Utah statutes
                amendment_patterns = [
                    r'Amended by Chapter \d+',
                    r'Repealed by Chapter \d+',
                    r'Effective \d{4}-\d{2}-\d{2}',
                    r'(\d{4}, c\. \d+.*?)(?=\n\n|\n[A-Z]|$)',
                    r'(\d{4} General Session.*?)(?=\n\n|\n[A-Z]|$)',
                    r'Enacted by Chapter \d+'
                ]
                
                statute_text = text_content
                statute_mods = ""
                
                # Find the first occurrence of any amendment pattern
                first_amendment_pos = len(text_content)
                for pattern in amendment_patterns:
                    match = re.search(pattern, text_content, re.DOTALL)
                    if match and match.start() < first_amendment_pos:
                        first_amendment_pos = match.start()
                
                if first_amendment_pos < len(text_content):
                    # Split at the first amendment
                    statute_text = text_content[:first_amendment_pos].strip()
                    statute_mods = text_content[first_amendment_pos:].strip()
                else:
                    # No amendments found, use entire content as statute text
                    statute_text = text_content.strip()
                    statute_mods = ""
                
                temp.loc[i,'statute_text'] = statute_text
                temp.loc[i,'statute_mods'] = statute_mods
                
                # Get universal citation
                citation_div = soup.find('div', class_='citation')
                if citation_div:
                    citation_span = citation_div.find('span')
                    if citation_span:
                        temp.loc[i,'universal_citation'] = citation_span.get_text()
                    else:
                        # Fallback citation format
                        title = temp.loc[i,'title']
                        chapter = temp.loc[i,'chapter']
                        section = temp.loc[i,'section']
                        temp.loc[i,'universal_citation'] = f"UT Code § {title}-{chapter}-{section} (2023)"
                else:
                    # Fallback citation format
                    title = temp.loc[i,'title']
                    chapter = temp.loc[i,'chapter']
                    section = temp.loc[i,'section']
                    temp.loc[i,'universal_citation'] = f"UT Code § {title}-{chapter}-{section} (2023)"
                    
        except Exception as e:
            print(f"Error processing Utah statute {temp.loc[i,'section_url']}: {e}")
            temp.loc[i,'statute_text'] = f'Error: {str(e)}'
            temp.loc[i,'statute_mods'] = ''
            temp.loc[i,'universal_citation'] = ''
        
temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Virginia.
temp=pd.DataFrame(columns=['index','state','title','chapter','section','section_url','url'])
section_list=['48','49','50','51','52','52.1','53','54','55','55.1','55.2','55.2:1','55.3','55.4','56','57','58','59','60','61','61.1']
section_list_url=['48','49','50','51','52','52-1','53','54','55','55-1','55-2','55-2-1','55-3','55-4','56','57','58','59','60','61','61-1']

k=0
for j in [2273,2274]:
    for i in range(0,len(section_list)):
        temp.loc[i+k*len(section_list)]=[j,'virginia','57','5',section_list[i],'57-'+section_list_url[i],'https://law.justia.com/codes/virginia/2023/title-57/chapter-5/section-57-'+section_list_url[i]+'/']
    k+=1

temp.loc[42]=[2273,'virginia','2-2','5','507.1','2-2-507-1','https://law.justia.com/codes/virginia/2023/title-2-2/chapter-5/section-2-2-507-1/']
temp.loc[43]=[2274,'virginia','2-2','5','507.1','2-2-507-1','https://law.justia.com/codes/virginia/2023/title-2-2/chapter-5/section-2-2-507-1/']

temp.loc[44]=[2295,'virginia','32-1','20','373','32-1-373','https://law.justia.com/codes/virginia/2023/title-32-1/chapter-20/section-32-1-373/']
temp.loc[45]=[2295,'virginia','32-1','20','374','32-1-374','https://law.justia.com/codes/virginia/2023/title-32-1/chapter-20/section-32-1-374/']
temp.loc[46]=[2295,'virginia','32-1','20','375','32-1-375','https://law.justia.com/codes/virginia/2023/title-32-1/chapter-20/section-32-1-375/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        
        # Get the main content
        content_div = soup.find('div', id='codes-content')
        if content_div:
            text_content=content_div.get_text(separator='</p><p>').split('</p><p>')
            temp.loc[i,'statute_text']=''.join(text_content[:-1])
            temp.loc[i,'statute_mods']=''.join(text_content[-1])
        
        cite_div=soup.find('div',class_='citation')
        if cite_div:
            temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

#Code repealed statutes to have blank statute text.
temp.loc[pd.isnull(temp.statute_text)==True,'statute_text']=''

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%Washington.
temp=pd.DataFrame(columns=['index','state','title','chapter','section','section_url','url'])
section_list=['100','105','107','110','115','130','135','140','175']

k=0
for j in [2372,2373]:
    for i in range(0,len(section_list)):
        temp.loc[i+k*len(section_list)]=[j,'washington','434','120',section_list[i],'434-120-'+section_list[i],'https://app.leg.wa.gov/WAC/default.aspx?cite=434-120-'+section_list[i]]
    k+=1

temp.loc[18]=[2372,'washington','19','09','020','19-09-020','https://law.justia.com/codes/washington/2023/title-19/chapter-19-09/section-19-09-020/']
temp.loc[19]=[2373,'washington','19','09','020','19-09-020','https://law.justia.com/codes/washington/2023/title-19/chapter-19-09/section-19-09-020/']

for i in range(1,10):
    temp.loc[i+19]=[2394,'washington','70','45','0'+f'{i}'+'0','70-45-'+'0'+f'{i}'+'0','https://law.justia.com/codes/washington/2023/title-70/chapter-70-45/section-70-45-'+'0'+f'{i}'+'0'+'/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        if temp.loc[i,'title']=='434':
            req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
            page = urlopen(req)
            html = page.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            text=soup.find('div',id='contentWrapper').get_text().split('[Statutory Authority:')
            
            temp.loc[i,'statute_text']=''.join(text[0].replace('PDF',''))
            temp.loc[i,'statute_mods']='[Statutory Authority:'+''.join(text[1])
            temp.loc[i,'universal_citation']='WAC 434-'+temp.loc[i,'chapter']+'-'+temp.loc[i,'section']
        else:
            url=temp.loc[i,'url']
            print(f"Fetching: {url}")
            req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
            page = urlopen(req)
            html = page.read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            soup.find('div',id='codes-content').get_text()
        
            #This separates text into statute and previous amendments to statute.
            text=soup.find('div',id='codes-content')
            text=text.get_text().split('[ ')
            temp.loc[i,'statute_text']=''.join(text[0])
            temp.loc[i,'statute_mods']='[ '+''.join(text[1])
            
            #This gets the universal citation.
            temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)

# %%West Virginia.
temp=pd.DataFrame(columns=['index','state','chapter','article','section','section_url','url'])
section_list=['1','1a','2','5','6','7','8','9','10','11','12','13','14','15','15a','15b']
for i in range(0,len(section_list)):
    temp.loc[i]=[2473,'west virginia','29','19',section_list[i],'29-19-'+section_list[i],'https://law.justia.com/codes/west-virginia/2023/chapter-29/article-19/section-29-19-'+section_list[i]+'/']
    
section_list=['1','1a','2','5','6']
for i in range(0,len(section_list)):
    temp.loc[i+16]=[2474,'west virginia','29','19',section_list[i],'29-19-'+section_list[i],'https://law.justia.com/codes/west-virginia/2023/chapter-29/article-19/section-29-19-'+section_list[i]+'/']

temp[['statute_text','statute_mods','universal_citation']]=''

#Get statute text.
for i in temp.index:
    if temp.loc[i,'section_url']!='nan':
        url=temp.loc[i,'url']
        print(f"Fetching: {url}")
        req  = urllib.request.Request(url, headers={'User-Agent': user_agent})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        soup.find('div',id='codes-content').get_text()
    
        #This separates text into statute and previous amendments to statute.
        text=soup.find('div',id='codes-content')
        if 'NOTE: ' in text.get_text():
            text=text.get_text(separator='</p><p>').split('</p><p>')
            temp.loc[i,'statute_text']=''.join(text[2:])
            temp.loc[i,'statute_mods']=''.join(text[1])
        else:
            text=text.get_text()
            temp.loc[i,'statute_text']=''.join(text)
            temp.loc[i,'statute_mods']=''
        
        #This gets the universal citation.
        temp.loc[i,'universal_citation']=soup.find('div',class_='citation').find('span').get_text()

temp_df=pd.concat([temp_df,temp],ignore_index=True)
temp_df.to_csv('multi_text_v1.csv',index=False)









