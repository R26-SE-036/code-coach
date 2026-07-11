public class GenMissingBreakBug165 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "paid";
            case 3:
                label = "expired";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
