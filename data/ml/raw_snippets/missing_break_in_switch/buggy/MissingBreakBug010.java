package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug010 {
    static String statusText(int code) {
        String text;
        switch (code) {
            case 200:
                text = "OK";
                break;
            case 404:
                text = "Not Found";
            case 500:
                text = "Server Error";
                break;
            default:
                text = "Unknown";
                break;
        }
        return text;
    }
}
