public class GenMissingBreakFix092 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "paid";
                break;
            case 4:
                label = "queued";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
