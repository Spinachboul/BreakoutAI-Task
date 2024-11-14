### **Overview**
This application is designed to serve as an **AI-powered data enrichment agent**. It allows users to upload data from either a **CSV file** or a **Google Sheet**, process the data by searching for additional information on the web, and use an **LLM (Large Language Model)** to extract relevant information. Users can specify custom query templates and output columns, making the application highly flexible for different use cases.

### **Key Features:**
1. **Data Input:** Supports data upload from a CSV file or Google Sheets.
2. **Data Processing:** Allows users to select a primary column and specify a query template for web searches.
3. **Integration with LLMs:** Uses an LLM to extract information from search results.
4. **Real-Time Progress:** Displays a progress bar to provide real-time feedback on data processing.
5. **Data Output:** Displays processed results in a table format with options to save the output back to Google Sheets.

### **Main Components:**

#### 1. **DataProcessor Class**
Handles data loading, preprocessing, and Google Sheets integration.

##### **Attributes:**
- `df`: DataFrame to hold the loaded data.
- `primary_column`: The column selected by the user as the primary column for processing.
- `google_creds`: Stores Google Sheets credentials for API access.

##### **Methods:**
- **`_load_google_credentials()`**:
  - Loads Google Sheets API credentials from a JSON file.
  - Returns an authenticated `Credentials` object.
- **`load_google_sheet(sheet_id: str) -> bool`**:
  - Loads data from a specified Google Sheet using its `sheet_id`.
  - Processes the data into a DataFrame and handles empty or missing values.
  - Returns `True` if successful, `False` otherwise.
- **`write_to_google_sheet(sheet_id: str, data: pd.DataFrame) -> bool`**:
  - Writes the processed DataFrame back to the specified Google Sheet.
  - Returns `True` if the operation succeeds.
- **`load_csv(file) -> bool`**:
  - Loads data from an uploaded CSV file and processes it into a DataFrame.
- **`get_columns() -> List[str]`**:
  - Returns a list of column names from the loaded DataFrame.
- **`get_value(row: pd.Series, column: str) -> str`**:
  - Safely retrieves the value of a specified column from a given row.

#### 2. **WebSearcher Class**
Handles web search functionality using an API to fetch search results.

##### **Attributes:**
- `api_key`: API key for the search service (e.g., SerpAPI).

##### **Methods:**
- **`search(query: str) -> List[Dict]`**:
  - Performs a web search using the specified query.
  - Returns a list of search results, each represented as a dictionary containing relevant information like title and snippet.

#### 3. **LLMProcessor Class**
Handles processing of search results using a Large Language Model (LLM).

##### **Attributes:**
- `client`: Instance of the LLM client (e.g., Groq API).

##### **Methods:**
- **`process_results(search_results: List[Dict], prompt: str) -> str`**:
  - Extracts information from search results based on a provided prompt.
  - Uses LLM to generate concise responses based on the search context.

#### 4. **process_entity Function**
Processes a single entity by creating a search query, fetching search results, and using the LLM to extract information.

##### **Parameters:**
- `entity`: The value from the primary column to be enriched.
- `query_template`: A template string where `{entity}` is replaced with the actual entity value.
- `searcher`: An instance of the `WebSearcher` class.
- `llm_processor`: An instance of the `LLMProcessor` class.

##### **Returns:**
- A dictionary containing the entity and the extracted information.

#### 5. **Main Function (`main()`)**
The core of the Streamlit application, providing the user interface and integrating all components.

##### **Workflow:**
1. **Title and Session Initialization**:
   - Initializes `DataProcessor` and `results` in the session state if not already present.
2. **Data Input**:
   - Allows users to choose between **CSV Upload** and **Google Sheets** input.
   - Loads the data into the DataFrame based on user input.
3. **Advanced Options**:
   - Lets users select the primary column and specify a query template for web search.
   - Allows specification of output columns for customized results.
4. **Data Processing**:
   - On clicking **"Process Data"**, iterates through each row of the DataFrame:
     - Retrieves the entity value.
     - Performs a search query and extracts information using LLM.
     - Updates the results list and progress bar dynamically.
   - Displays the final results in a table format.
5. **Save to Google Sheets**:
   - Provides an option to save the processed results back to a specified Google Sheet.

#### **Progress Bar Implementation**
- The progress bar is implemented using `st.progress()`, providing real-time feedback during data processing:
  ```python
  progress_bar = st.progress(0)
  total_rows = len(st.session_state.data_processor.df)
  for idx, row in st.session_state.data_processor.df.iterrows():
      progress_bar.progress((idx + 1) / total_rows)
  ```

### **Environment Variables (`env_vars`)**
Stores sensitive configuration values such as:
- `SERPAPI_KEY`: API key for SerpAPI web search.
- `GROQ_API_KEY`: API key for Groq's LLM service.

### **Configuration File (`config.py`)**
A Python file containing environment variable definitions, typically loaded using `os.environ` or similar methods.

### **Google Sheets Integration**
Uses the **Google Sheets API** for data loading and writing:
- Requires a JSON credentials file for authentication (`service_account.json`).
- Scopes required: `https://www.googleapis.com/auth/spreadsheets`.

### **Dependencies**
- **Streamlit**: For building the user interface.
- **Pandas**: For data manipulation and DataFrame operations.
- **Google API Client**: For Google Sheets interaction.
- **Requests**: For handling HTTP requests to the web search API.
- **Datetime**: For handling date and time operations.
- **Groq API**: For interacting with the LLM.

### **Usage Instructions**
1. **Install Required Packages**:
   ```
   pip install streamlit pandas google-api-python-client google-auth requests groq
   ```
2. **Run the Application**:
   ```
   streamlit run app.py
   ```
3. **Input Options**:
   - Upload a CSV file or provide a Google Sheet ID for data input.
   - Specify the primary column, query template, and output columns.
4. **Process Data**:
   - Click **"Process Data"** to start enrichment.
   - Monitor the progress with the real-time progress bar.
   - View the processed results in the data table.
