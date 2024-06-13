# app.py

import pandas as pd
from shiny import reactive
from shiny.express import render, input, ui
import faicons as fa

# Prepare initial table
df = pd.DataFrame({
    'Job Description': ["A", "B", "C"],
    'Size': [4, 5, 6],
    'Value': [1, 2, 3],
    'Urgency': [1, 2, 3],
    'Risk Reduction': [0, 0, 0],
    'Opportunity': [0, 0, 0]
})

empty_row = {
    'Job Description': "",
    'Size': 0,
    'Value': 0,
    'Urgency': 0,
    'Risk Reduction': 0,
    'Opportunity': 0
}

column_names = df.columns
tbl = reactive.value(df)

# Helpers
def cell_to_int(s, column):
    try:
        result = int(s)
    except ValueError:
        raise SafeException(
                "{column} values should be integers."
            )
    if result > 0:
        return result
    else:
        raise SafeException("{column} values should be non-zero, positive integers.")

# Set up the UI

ui.page_opts(fillable=True)

with ui.layout_columns(col_widths=(8, 4, 12)):
    ui.markdown(
        """
        **What is Weighted Shortest Job First?**")

        Weighted Shortest Job First (WSJF) is a method for prioritizing work 
        that optimizes the rate at which your team delivers value. In other words, 
        WSJF prioritizes quick wins and important jobs. It grades tasks on the 
        following traits:

        - **Job Size** - How Much time or capacity does the job require?
        - **Business/User Value** - How much value will the job deliver when completed?
        - **Urgency** - What value do we permanently lose by delaying the task?
        - **Risk Reduction** - Will doing the task now reduce the risk of not delivering on this task or another in the future?
        - **Opportunity Enablement** - Will doing the taks create new opportunities, for example from what we learn?
        """
    )

    with ui.card():
        # Display next job
        with ui.value_box(showcase=fa.icon_svg("circle-check", "regular")):
            "Next Job"

            @render.text
            def next_job():
                return top_job()

    with ui.card():
        ui.card_header("WSJF Calculator")
        ui.markdown(
            "**Instructions**: Add your jobs by editing the rows below. Choose values relative to the other tasks."
        )
        with ui.layout_columns(col_widths=(8, 4)):
            # Make editable table
            @render.data_frame
            def jobs():
                return render.DataGrid(tbl.get(), editable=True)

            @render.data_frame
            def wsjf():
                return priorities()[['WSJF']]

            ui.input_action_button("add_row", "Add Row", width = '200px')



@jobs.set_patch_fn
def upgrade_patch(*, patch: CellPatch,):
    if patch["column_index"] >= 1: 
        return cell_to_int(patch["value"], column_names[patch["column_index"]])
    else:
        return patch["value"]

@reactive.calc
def priorities():
    df2 = pd.DataFrame(jobs.data_view())

    # Handle types
    df2['Size'] = df2['Size'].astype(int)
    df2['Urgency'] = df2['Urgency'].astype(int)
    df2['Risk Reduction'] = df2['Risk Reduction'].astype(int)
    df2['Opportunity'] = df2['Opportunity'].astype(int)

    # Calculate Cost of Delay
    df2['Cost of Delay'] = df2['Urgency'] + df2['Risk Reduction'] + df2['Opportunity']

    # Filter rows where 'Size' is greater than 0
    df_filtered = df2[(df2['Size'] > 0)]

    # Calculate new WSJF
    df_filtered['rd'] = df_filtered['Size'] / df_filtered['Size'].min()
    df_filtered['cod'] = df_filtered['Cost of Delay'] / df_filtered['Cost of Delay'].min()
    df_filtered['WSJF'] = df_filtered['cod'] / df_filtered['rd']

    return df_filtered[['Job Description', 'WSJF']]

# Let user add rows
@reactive.effect
@reactive.event(input.add_row)
def _():
    jobs.data_view()
    new_tbl = priorities()._append(empty_row, ignore_index=True) 
    tbl.set(new_tbl)
    return None



@reactive.calc
def top_job():
    return priorities().sort_values(by='WSJF', ascending=False)['Job Description'].iloc[0]


