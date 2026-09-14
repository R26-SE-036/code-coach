package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug014 {
    static String season(int month) {
        String season = "";
        switch (month) {
            case 12:
            case 1:
            case 2:
                season = "Summer";
            case 3:
            case 4:
            case 5:
                season = "Autumn";
                break;
            case 6:
            case 7:
            case 8:
                season = "Winter";
                break;
            default:
                season = "Spring";
        }
        return season;
    }
}
