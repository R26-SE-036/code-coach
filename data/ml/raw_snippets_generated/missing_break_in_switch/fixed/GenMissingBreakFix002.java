public class GenMissingBreakFix002 {
    static String describeItem(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "closed";
                break;
            case 4:
                label = "final";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
