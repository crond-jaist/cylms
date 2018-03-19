class Storyboard:
    # Config file constants
    DEFAULT_CONFIG_FILE = "config_example"
    CONFIG_SECTION = "config"
    CONFIG_ENABLE_COPY = "enable_copy"
    CONFIG_INPUT_FILE = "input_file"
    CONFIG_PACKAGE_NAME = "package_name"
    CONFIG_REMOTE_LMS = "remote_lms"
    CONFIG_DESTINATION = "destination"

    # Content description file constants
    ## Top section about training
    KEY_TRAINING = "training"
    KEY_ID = "id"
    KEY_TITLE = "title"
    KEY_OVERVIEW = "overview"
    KEY_LEVEL = "level"
    KEY_QUESTIONS = "questions"

    ## Sub-section about questions
    #KEY_ID = "id"
    KEY_TYPE = "type"
    VALUE_TYPE_FILL_IN = "fill-in"
    VALUE_TYPE_CHOICE = "choice"
    VALUE_TYPE_NUMERIC = "numeric"
    KEY_BODY = "body"
    KEY_CHOICES = "choices"
    KEY_ANSWER = "answer"
    KEY_HINTS = "hints"

    # Tags in SCORM package
    ## Tag below appears in Template/imsmanifest.xml
    TAG_TRAINING_ID = "training_id"

    ## Tags below appear in Template/shared/assessmenttemplate.html
    TAG_TRAINING_LEVEL = "training_level"
    TAG_TRAINING_TITLE = "training_title"
    TAG_TRAINING_OVERVIEW = "training_overview"

    ## Tags below appear in Template/Playing/questions.js
    TAG_QUESTION_ID = "questionId"
    TAG_QUESTION_BODY = "questionBody"
    TAG_QUESTION_TYPE = "questionType"
    TAG_QUESTION_ANSWER = "questionAnswer"
    TAG_QUESTION_CORRECT_ANSWER = "questionCorrectAnswer"
    TAG_QUESTION_OBJECTIVE_ID = "questionObjectiveId"
