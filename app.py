# app.py

import pandas as pd
import faicons as fa
from shiny import reactive
from shiny.express import render, input, ui
from shinyswatch import theme

# Prepare initial table
df = pd.DataFrame({
    'Job Description': ["Submit TPS Report", "Write Cover Sheet", "Make Coffee"],
    'Size': [3, 1, 1],
    'Value': [5, 0, 1],
    'Urgency': [1, 0, 1],
    'Risk Reduction': [3, 1, 1],
    'Opportunity': [1, 0, 0]
})

empty_row = {
    'Job Description': "",
    'Size': 1,
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
    if column == 'Size' and result < 1 :
        raise SafeException("Size values should be positive, non-zero integers.")
    else:
        return result

def wsjf_norm(x):
    if (x == 0).any():
        return x
    else:
        return x / x.min()

# Set up the UI

ui.page_opts(fillable=True)

with ui.layout_columns(col_widths=(8, 4, 12)):
    ui.markdown(
        """
        **What is Weighted Shortest Job First?**

        Weighted Shortest Job First (WSJF) is a method for prioritizing work 
        that optimizes the rate at which your team delivers value. 
        WSJF prioritizes quick wins and important jobs. It grades tasks on the 
        following traits:

        - **Job Size** - How Much time or capacity does the job require?
        - **Business/User Value** - How much value will the job deliver when completed?
        - **Urgency** - What value do we permanently lose by delaying the task?
        - **Risk Reduction** - Will doing the task now reduce the risk of not delivering on this or another task in the future?
        - **Opportunity Enablement** - Will doing the task create new opportunities, for example from what we learn?
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
        ui.card_header("Calculator")
        ui.markdown(
            "**Instructions**: Add your jobs by editing the rows below. Choose values relative to the other tasks."
        )
        with ui.layout_columns(col_widths=(10, 2)):
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

    # Calculate new WSJF
    df2['rd'] = wsjf_norm(df2['Size'])
    df2['cod'] = wsjf_norm(df2['Cost of Delay'])
    df2['WSJF'] = df2['cod'] / df2['rd']

    return df2[['Job Description', 'WSJF']]

# Let user add rows
@reactive.effect
@reactive.event(input.add_row)
def _():
    new_tbl = jobs.data_view()._append(empty_row, ignore_index=True) 
    tbl.set(new_tbl)
    return None



@reactive.calc
def top_job():
    return priorities().sort_values(by='WSJF', ascending=False)['Job Description'].iloc[0]


