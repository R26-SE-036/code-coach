public class GenMissingBreakFix028 {
    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "queued";
                break;
            case 4:
                label = "expired";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
