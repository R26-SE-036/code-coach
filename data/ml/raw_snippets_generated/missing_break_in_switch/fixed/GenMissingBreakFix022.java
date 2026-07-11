public class GenMissingBreakFix022 {
    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "new";
                break;
            case 4:
                label = "archived";
                break;
            case 5:
                label = "final";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
