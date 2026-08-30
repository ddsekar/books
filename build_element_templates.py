import pandas as pd
import json
import os

def build_element_templates(excel_file_path, output_dir="dist"):
    xls = pd.ExcelFile(excel_file_path)
    
    df_templates = pd.read_excel(xls, 'Templates')
    df_actions = pd.read_excel(xls, 'Actions') if 'Actions' in xls.sheet_names else None
    df_inputs = pd.read_excel(xls, 'Inputs')
    df_outputs = pd.read_excel(xls, 'Outputs') if 'Outputs' in xls.sheet_names else None
    df_conditions = pd.read_excel(xls, 'Conditions') if 'Conditions' in xls.sheet_names else None

    os.makedirs(output_dir, exist_ok=True)
    all_generated_templates = []

    for _, t in df_templates.iterrows():
        t_id = t['template_id']
        properties = []

        # 1. Process Actions & Dynamic Job Types
        if df_actions is not None:
            t_actions = df_actions[df_actions['template_id'] == t_id]
            if not t_actions.empty:
                choices = [
                    {"name": row['action_label'], "value": row['job_type']}
                    for _, row in t_actions.iterrows()
                ]
                properties.append({
                    "id": "action_selector",
                    "label": "Action / Operation",
                    "type": "Dropdown",
                    "value": choices[0]['value'],
                    "choices": choices,
                    "binding": {"type": "zeebe:taskDefinition", "property": "type"}
                })

        # 2. Process Inputs
        t_inputs = df_inputs[df_inputs['template_id'] == t_id]
        for _, inp in t_inputs.iterrows():
            prop = {
                "id": inp['prop_id'],
                "label": inp['label'],
                "type": inp['type'],
                "binding": {"type": "zeebe:input", "name": inp['prop_id']}
            }
            if pd.notna(inp.get('feel')) and inp['feel'] != 'none':
                prop['feel'] = inp['feel']
            if pd.notna(inp.get('default_value')):
                prop['value'] = inp['default_value']

            # Attach Action Condition
            if pd.notna(inp.get('action_id')) and df_actions is not None:
                matched_action = df_actions[
                    (df_actions['template_id'] == t_id) & 
                    (df_actions['action_id'] == inp['action_id'])
                ]
                if not matched_action.empty:
                    job_type_val = matched_action.iloc[0]['job_type']
                    prop['condition'] = {"property": "action_selector", "equals": job_type_val}

            properties.append(prop)

        # Build JSON Schema structure
        template_json = {
            "$schema": "https://unpkg.com/@camunda/zeebe-element-templates-json-schema/resources/schema.json",
            "name": t['name'],
            "id": t['template_id'],
            "appliesTo": [t['applies_to']],
            "elementType": {"value": t['applies_to']},
            "properties": properties
        }

        all_generated_templates.append(template_json)
        
        # Write individual JSON file for Web Modeler
        with open(f"{output_dir}/{t_id}.json", "w") as f:
            json.dump(template_json, f, indent=2)

    # Write single combined JSON for Desktop Modeler
    with open(f"{output_dir}/element-templates.json", "w") as f:
        json.dump(all_generated_templates, f, indent=2)

    print(f" Successfully generated {len(all_generated_templates)} element templates.")

if __name__ == "__main__":
    build_element_templates("Connectors.xlsx")
