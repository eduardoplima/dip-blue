from typing import Optional, List
from pydantic import BaseModel, Field

from langchain.prompts import PromptTemplate, ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI

class MultaPydantic(BaseModel):
  """Determinação de multa, com valor e responsável"""
  pessoa_responsavel: str = Field(description="Nome do responsável pela multa")
  valor: float = Field(description="Valor da multa")

class ObrigacaoPydantic(BaseModel):
  """Determinação de obrigação, com valor e responsável"""
  orgao_responsavel: str = Field(description="Nome do órgão ou gestor responsável pela obrigação")
  descricao: str = Field(description="Texto descritivo da obrigação")
  prazo_obrigacao: str = Field(description="Prazo para cumprimento da obrigação")

class DecisaoPydantic(BaseModel):
  """Decisão processual do TCE/RN"""
  determinacoes: List[Optional[MultaPydantic | ObrigacaoPydantic]] = Field(description="Determinação de multa ou obrigação")
  

def classificar_determinacao_outro(decisao, llm: ChatOpenAI):
  examples = [
      {
          "input": """
          - Adoção das providências cabíveis no tocante aos indícios de impropriedades /irregularidades
  elencadas na tabela 19 do Relatório (transcritas acima ), com fundamento no art. 2º, inciso III, da
  Resolução nº 012/2023-TCE, notadamente para que a Secretaria de Controle Externo analise a
  capacidade operacional desta Corte com vistas ao acompanhamento e /ou à abertura de processo
  autônomo, respeitadas a conveniência e oportunidade, referente aos itens 4.2 (Divergência dos
  dados do planejamento do Projeto, Inconsistência dos saldos da conta bens móveis entre os
  registros do SIGEF - Sistema Integrado de Planejamento e Gestão Fiscal - e SMI - Sistema de
  Monitoramento e Informações do Projeto - e deficiências na elaboração das notas explicativas ),
  5.5.1.1 (Inventário físico ), 5.6.1.1 ( Falhas/deficiências construtivas do Hospital Regional da
  Mulher Parteira Maria Correia) e 5.6.1.3 (Pendências de legalização das obras da Biblioteca
  Câmara Cascudo e da Sede do Serviço Nacional de Emprego – SINE).""",
          "output": "DETERMINACAO"}, {
          "input": """( a.i) promovam, no prazo de 120 (cento e vinte dias) úteis, contados a partir da intimação da
  presente Decisão, a apuração dos fatos e se verifique a constitucionalidade e legalidade dos
  vínculos funcionais de cada servidor que figura nos Anexos nºs. 01 e 02 contidos nos Eventos
  nºs. 04 e 05, além de outros que porventura sejam informados pela DDP em cumprimento ao
  item b, por meio da instauração de processos administrativos disciplinares individuais ,
  regulados pela Lei que trata do Estatuto Jurídico dos Servidores do respectivo Município ,
  com observância dos princípios do contraditório, ampla defesa e devido processo legal;
    ( a.ii) comprovem neste feito, em 05 dias úteis após ultimado o prazo de definição dos PAD
  ´s, as conclusões de todos os processos administrativos instaurados, no tocante à eliminação
  de tríplice vínculo funcional identificado e de enquadramento das eventuais acumulações
  dúplices nas hipóteses permitidas pela Constituição Federal, com a respectiva
  compatibilidade de horários, sob pena de, não cumprindo tais obrigações nos prazos antes
  referidos, incidir em multa diária e pessoal ao gestor, no valor de R$ 500,00, com espeque no
  art. 110 da LCE nº 464/2012 c/c o art. 326 do RITCE, cabendo à Diretoria de Despesa com
  Pessoal monitorar o cumprimento da presente Decisão;""",
          "output": "DETERMINACAO"}, {
          "input": """Vistos, relatados e discutidos estes autos, em consonância ao posicionamento do
  Corpo técnico e do Ministério Público de Contas, ACORDAM os Conselheiros, nos termos
  do voto proposto pelo Conselheiro Relator, julgar a inadmissibilidade da presente denúncia e
  o seu conseqüente arquivamento, com fulcro nos art. 12 do Provimento 002/2020 –
  CORREG/TCE, aprovado pela Resolução 016/2020 – TCE e artigo 80, § 1º, da LOTCE.
  E ainda, Pela expedição de RECOMENDAÇÃO, nos termos do art. 301, III da Resolução
  009/2012 (RITCE/RN) c/c art. 13, II da Resolução 16/2020 –TCE/RN, ao Executivo
  Municipal de Nísia Floresta /RN, com cópia para o respectivo órgão de controle interno, ou
  setor responsável pelas publicações oficiais, lastreada na Constituição Federal de 88/ Art. 37,
  a fim de que promova e deixe claro os seguintes comportamentos em suas postagens""",
          "output": "DETERMINACAO"},{
          "input": """Vistos, relatados e discutidos estes autos, concordando com o proposto pelo Corpo
  Técnico e pelo órgão Ministerial de Contas, ACORDAM os Conselheiros, nos termos do voto
  proferido pelo Conselheiro Relator, julgar pela irregularidade da matéria, nos termos do art .
  75, inciso I, da Lei Complementar nº 464/2012, condenando o gestor responsável, Sr. Thiago
  Meira Mangueira, ao pagamento de multa no valor de R$ 18.774,51 (dezoito mil setecentos e
  setenta e quatro reais e cinquenta e um centavos ), conforme previsto no art. 21, inciso I ,
  alínea ‘a’ e § 1º, da Resolução nº 012/2016-TCE c /c o art. 107, inciso II, alínea “a” da Lei
  Complementar nº 464/2012. """,
          "output": "DETERMINACAO"},
          {
              "input": """Vistos, relatados e discutidos estes autos, acolhendo os fundamentos do parecer
  ministerial, com substrato no art. 209 V da norma regimental, ACORDAM os Conselheiros ,
  nos termos do voto proposto pela Conselheira Relatora, julgar pelo ARQUIVAMENTO dos
  autos.""",
              "output": "OUTROS",
          },
          {
              "input": """Vistos, relatados e discutidos estes autos, ACORDAM os Conselheiros,  com o
  impedimento do Conselheiro Presidente Renato Costa Dias, nos termos do voto profposto
  pela Conselheira Relatora, haja vista os fundamentos fático -jurídicos explanados no excerto
  antecedente, comprovado documentalmente o adimplemento substancial do plano de
  redimensionamento/adequação do sistema de ensino natalense, julgar pela EXTINÇÃO do
  FEITO nos termos do art. 71 da Lei Complementar (estadual) c/c art. 22 §1° da LINDB e art .
  209 V da regra regimental.""",
              "output": "OUTROS",
          },
          {
              "input": """Vistos, relatados e discutidos estes autos, em consonância com o posicionamento da
  Diretoria de Administração Municipal – DAM e do Ministério Público de Contas ,
  ACORDAM os Conselheiros, nos termos do voto proferido pelo Conselheiro Relator, julgar
  pelo reconhecimento da incidência da Prescrição Intercorrente sobre a pretensão punitiva e
  ressarcitória desta Corte de Contas, nos termos do artigo 111, parágrafo único, da Lei
  Complementar Estadual nº 464/2012, com o consequente arquivamento dos presentes autos.
  E ainda, pelo envio de cópia das principais peças dos autos ao Ministério Público Estadual ,
  para conhecimento e atuação no âmbito de sua competência.""",
              "output": "OUTROS",
          },
          {
              "input": """Vistos, relatados e discutidos estes autos, em dissonância com o Ministério Público
  de Contas, ACORDAM os Conselheiros, nos termos do voto proferido pelo Conselheiro
  Relator, julgar pela extinção do feito, sem julgamento de mérito, com o consequente
  ARQUIV AMENTO dos autos, em virtude da incompatibilidade entre a emissão de parecer
  prévio pela aprovação com ressalvas das contas de governo e a instauração de apuração de
  responsabilidade para aplicação de sanções.""",
              "output": "OUTROS",
          }
  ]

  example_prompt = ChatPromptTemplate.from_messages([
        ("human", '''
         {input} '''),
        ("ai", "{output}"),
    ])

  few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,)

  final_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """Você é um classificador de decisões de um tribunal de contas.
         Sua tarefa é definir se uma decisão trata de uma multa ou obrigação
         de fazer.

         Responda com DETERMINACAO se o texto contiver o termo "multa" e alguma recomendação ou obrigação de fazer
         Responda com OUTROS se o texto tratar de arquivamento, extinção do feito ou prescrição da matéria, ou outro assunto que não seja DETERMINACAO

         Responda APENAS com DETERMINACAO ou OUTROS."""),
        few_shot_prompt,
        ("human", "{input}"),])

  chain = final_prompt | llm
  decision_type = chain.invoke({"input": decisao}).content
  return decision_type

def classificar_itens_decisao(decisao, llm: ChatOpenAI):
  prompt = PromptTemplate.from_template("""
  Você é um agente que identifica listas de determinações em textos de decisões. Seu objetivo
  é extrair um conjunto de textos de uma lista que contém obrigações ou imposições de multas. Se não houver
  determinações, responda apenas com "N/D"

  Decisão : {input}

  Sua resposta:
  """)

  structured_llm = llm.with_structured_output(schema=DecisaoPydantic)
  chain = prompt | structured_llm
  return chain.invoke(decisao)
  