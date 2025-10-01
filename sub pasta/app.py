import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px

# --- Função de cálculo detalhado do IRPF ---
def calcular_irpf_completo(salario_mensal, inss=0, dependentes=0, despesas_medicas=0, despesas_educacao=0, pensao_alimenticia=0):
    deducao_dependente = dependentes * 220.0
    base_calculo = salario_mensal - inss - deducao_dependente - despesas_medicas - despesas_educacao - pensao_alimenticia
    if base_calculo < 0:
        base_calculo = 0

    faixas = [
        (0, 2500, 0.0),
        (2500.01, 3750, 7.5),
        (3750.01, 5000, 15.0),
        (5000.01, 6250, 22.5),
        (6250.01, float('inf'), 27.5)
    ]

    imposto_total = 0.0
    detalhes_faixas = []

    for limite_inferior, limite_superior, aliquota in faixas:
        if base_calculo > limite_inferior:
            valor_faixa = min(base_calculo, limite_superior) - limite_inferior
            imposto_faixa = valor_faixa * (aliquota / 100)
            imposto_total += imposto_faixa
            detalhes_faixas.append({
                "Faixa": f"{limite_inferior:.2f} - {limite_superior if limite_superior != float('inf') else 'inf'}",
                "Alíquota (%)": aliquota,
                "Base da Faixa (R$)": valor_faixa,
                "Imposto Faixa (R$)": imposto_faixa
            })

    return imposto_total, detalhes_faixas, base_calculo

# --- Configuração da página ---
st.set_page_config(page_title="Simulador Completo de IRPF", layout="wide")

st.title("💰 Simulador Completo de IRPF")

# --- Sidebar para entradas ---
st.sidebar.header("Configurações Gerais")
salario = st.sidebar.number_input("Salário Mensal (R$)", min_value=0.0, value=5000.0)
num_cenarios = st.sidebar.number_input("Número de Cenários", min_value=1, value=1, step=1)

st.sidebar.subheader("Configuração dos Cenários")
lista_cenarios = []
for i in range(1, num_cenarios + 1):
    st.sidebar.markdown(f"**Cenário {i}**")
    inss = st.sidebar.number_input(f"INSS - Cenário {i} (R$)", min_value=0.0, value=500.0)
    dependentes = st.sidebar.number_input(f"Dependentes - Cenário {i}", min_value=0, value=0)
    despesas_medicas = st.sidebar.number_input(f"Despesas Médicas - Cenário {i} (R$)", min_value=0.0, value=0.0)
    despesas_educacao = st.sidebar.number_input(f"Despesas Educação - Cenário {i} (R$)", min_value=0.0, value=0.0)
    pensao = st.sidebar.number_input(f"Pensão Alimentícia - Cenário {i} (R$)", min_value=0.0, value=0.0)
    lista_cenarios.append({
        "inss": inss,
        "dependentes": dependentes,
        "despesas_medicas": despesas_medicas,
        "despesas_educacao": despesas_educacao,
        "pensao_alimenticia": pensao
    })

# --- Cálculo do IRPF ---
if st.button("Calcular IR"):
    resultados = []
    detalhes_cenarios = []

    for idx, cenario in enumerate(lista_cenarios, 1):
        imposto, detalhes, base = calcular_irpf_completo(
            salario,
            inss=cenario["inss"],
            dependentes=cenario["dependentes"],
            despesas_medicas=cenario["despesas_medicas"],
            despesas_educacao=cenario["despesas_educacao"],
            pensao_alimenticia=cenario["pensao_alimenticia"]
        )
        resultados.append({
            "Cenário": f"Cenário {idx}",
            "Imposto Mensal (R$)": imposto,
            "Imposto Anual (R$)": imposto * 12,
            "Base de Cálculo (R$)": base
        })
        detalhes_cenarios.append((f"Cenário {idx}", detalhes))

    df_resultados = pd.DataFrame(resultados)

    # --- Resumo comparativo ---
    st.subheader("📊 Resumo Comparativo dos Cenários")
    st.dataframe(df_resultados)

    # --- Gráfico de imposto mensal ---
    st.subheader("📈 Comparativo de Imposto Mensal")
    fig_total = px.bar(df_resultados, x="Cenário", y="Imposto Mensal (R$)", text="Imposto Mensal (R$)",
                       labels={"Imposto Mensal (R$)": "Imposto Mensal (R$)"},
                       title="Imposto Mensal por Cenário")
    st.plotly_chart(fig_total)

    # --- Gráficos detalhados por faixa ---
    st.subheader("📊 Contribuição de Cada Faixa de Imposto")
    for nome_cenario, detalhes in detalhes_cenarios:
        df_faixas = pd.DataFrame(detalhes)
        fig_faixa = px.bar(df_faixas, x="Faixa", y="Imposto Faixa (R$)", text="Imposto Faixa (R$)",
                           labels={"Imposto Faixa (R$)": "Valor do Imposto (R$)"},
                           title=f"{nome_cenario} - Imposto por Faixa")
        st.plotly_chart(fig_faixa)

    # --- Download Excel ---
    def gerar_excel(df_resultados, detalhes_cenarios):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_resultados.to_excel(writer, sheet_name="Resumo Cenários", index=False)
            for nome_cenario, detalhes in detalhes_cenarios:
                pd.DataFrame(detalhes).to_excel(writer, sheet_name=nome_cenario, index=False)
            writer.save()
        return output.getvalue()

    excel_data = gerar_excel(df_resultados, detalhes_cenarios)
    st.download_button(
        label="📥 Baixar Relatório Excel",
        data=excel_data,
        file_name="simulacao_irpf_completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
         
     )