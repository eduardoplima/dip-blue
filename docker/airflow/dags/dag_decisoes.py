import datetime

from airflow import DAG
from airflow.models import Variable

from custom.operators import DecisaoOperator

with DAG(
    dag_id="dag_decisoes",
    schedule_interval="0 0 * * *",
    start_date=datetime.datetime(2022, 1, 1),
    catchup=False,
) as dag:
    data_inicio = Variable.get("decisoes_data_inicio")
    data_fim = Variable.get("decisoes_data_fim")

    decisao_operator = DecisaoOperator(
        task_id="decisao_operator",
        pdf_dir=Variable.get("decisoes_pdf_dir"),
    )

    decisao_operator.execute(data_inicio, data_fim)