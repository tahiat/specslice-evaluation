from string import Template
import os

class TableGenerator:
    def __init__ (self, data_list):
        self._table_data_list = data_list

    
    def _getHTMLTemplate(self):
        html_template = '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Specimin Evalutaion Result</title>
                </head>
                <body>

                <h2>SPECIMIN Evalutaion Result</h2>

                <table border="1">
                    <thead>
                        <tr>
                            <th>Issue Name</th>
                            <th>Status</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        $body
                    </tbody>
                </table>

                </body>
                </html>
            '''
        return html_template

    def generateTable(self):
        table_rows = ''
        for item in self._table_data_list:
            table_rows += f'''
                <tr>
                    <td>{item.name}</td>
                    <td>{item.status}</td>
                    <td><a href="{item.reason.replace("ISSUES/", "")}">{item.reason}</a></td>
                </tr>
            '''
        template = Template(self._getHTMLTemplate())
        output_html = template.safe_substitute(body=table_rows)
        with open('ISSUES/output.html', 'w') as file:
            file.write(output_html)
        print("HTML generated successfully.")