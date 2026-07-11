public class GenMissingBreakBug068 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "expired";
            case 4:
                label = "new";
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
