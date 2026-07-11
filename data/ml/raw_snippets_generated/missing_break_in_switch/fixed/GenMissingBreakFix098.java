public class GenMissingBreakFix098 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "paid";
                break;
            case 3:
                label = "new";
                break;
            case 4:
                label = "expired";
                break;
            case 5:
                label = "shipped";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
