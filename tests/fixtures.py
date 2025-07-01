import pytest
import os
from fastapi.testclient import TestClient
from src.executor import Summarizer, TaskManager,SummaryConfig
from src.endpoints import app

@pytest.fixture
def summarizer():
    if any([os.getenv('OPENAI_API_KEY')==None, os.getenv('LLM_MODEL')==None]):
        pytest.fail(reason='Environment variables OPENAI_API_KEY/LLM_MODEL is missing')
    summarizer = Summarizer(
        os.getenv("OPENAI_API_KEY"),
        SummaryConfig(
            model = os.getenv('LLM_MODEL'),
        )
    )
    return summarizer


@pytest.fixture
def client():
    client = TestClient(app)
    return client

@pytest.fixture
def task_manager():
    task_manager = TaskManager()
    return task_manager


@pytest.fixture
def paragraphs():
    return [
        "Event ID 2950 took place on 2024-09-28 at Talkatora. The event, categorized as 'Condolences Meeting', was attended by Rahul Gandhi(mainleader)( member of AICC) and organized by CPI-M. The attendance ranged between 500 and 1000 people. Here is a brief note about the event: Today condolence meeting for Late Sita Ram Yechury(CPIM) was held at Talkatora Indoor Stadium.The condolence meeting was attended by Smt. Vandana Karat,Shri Prakash Karat(CPIM), Shri Rahul Gandhi, Sh. Mallikarjun Khadge(AICC), Sh. D Raja(CPI)Sh. Ramgopal Yadav(SP), Smt. Supriya Sulle(NCP), Sh. Farrukh Abdullah, Sh. Manoj Jha, Gopal Rai(AAP) and other political party leaders.. The event has the demand Meeting. The event concluded with the following remark: No additional remark.",
        "Event ID 1906 took place on 2024-07-19 at Ramlila ground. The event, categorized as 'Dharna', was attended by Rahul Gandhi(mainleader)( member of INC) and organized by INC. The attendance ranged between 50 and 60 people. Here is a brief note about the event: 500 aadami is bare mein baten kar rahe hain . The event has the demand EVM machine. The event concluded with the following remark: No additional remark.",
        "Event ID 1452 took place on 2024-05-12 at Jawahar Bhawan new Delhi.. The event, categorized as 'Election agendas', was attended by Rahul Gandhi(mainleader)( member of AICC) and organized by AICC. The attendance ranged between 150 and 200 people. Here is a brief note about the event: The scheduled program no 03 of AICC was held at Jawahar Bhawan on Dr. Rajendra Prasad Road. The cultural and musical program started at 3:40 PM with a gathering of 150-200 people. At 5:00 PM, Shri Rahul Gandhi ji arrived at Jawahar Bhawan and joined the program. He spoke about Agniveer and then 8-10 students presented their problems based on questions. They raised issues such as employment, education, unemployment, hostel fees, and jobs that have been closed, and requested that they be reopened. Shri Rahul Gandhi ji assured everyone that if our government is formed, we will resolve all these issues and take the oath of the constitution. The program ended at 6:30 PM after he left Jawahar Bhawan, and the program concluded peacefully with a gathering of 150-200 people.. The event has the demand Agniveer, unemployment, education, inflation. The event concluded with the following remark: No additional remark.",
        "Event ID 1407 took place on 2024-05-10 at Jai Singh. The event, categorized as 'Demotration', was attended by Rahul Gandhi(mainleader)( member of INC) and organized by INC. The attendance ranged between 100 and 200 people. Here is a brief note about the event: General Election 2024 in view of being held for a longer period, protests against the Chief Election Commissioner. The event has the demand Genrel Election loksabha 2024. The event concluded with the following remark: No additional remark.",
        ]


@pytest.fixture
def task_id():
    return 'test_123'

@pytest.fixture
def secondary_summaries():
    return ["""Event Overview: Khadim-e-Zehra Committee Majlis-e-Aza\n\nOn 05.12.2024, the Khadim-e-Zehra Committee would organize a Majlis-e-Aza (Religious Programme) at Shia Jama Masjid, Kashmere Gate, in the jurisdiction of PS Kashmiri Gate, North District, Delhi.
            The programme, led by Syed Salman Ali Zaidi (M- 7982344071), would commence at 1930 hrs and continue until the completion of the event. The event is expected to gather around 900/1000 persons, including ladies and children, and would feature religious discourses by Maulanas.
            Following the Majlis, a procession would be taken out from Shia Jama Masjid to Dargah Panja Sharief, Kashmere Gate via Hamilton Road, Bara Bazar, Chabi Ganj & Chhota Bazar, covering a distance of 700/800 meters. The procession would include an Alam (Islamic flag) and a Taboot (Symbolic Coffin of Fatima Zehra)"""]

@pytest.fixture
def system_prompt():
    return """Create a polished final summary that integrates all major themes and insights.
            Ensure perfect flow and preserve all critical details"""

@pytest.fixture
def primary_prompt():
    return """You are a precise text analyzer performing the first phase of a nested map-reduce summarization.
            Create a summary from the sections"""

@pytest.fixture
def secondary_reduction_prompt():
    return """Create a coherent summary from the sections"""

@pytest.fixture
def final_reduction_prompt():
    return """You are performing the final phase of a nested map-reduce summarization.
        Create a final summary encapsulating all data details"""