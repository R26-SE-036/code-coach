public class GenMissingBreakBug126 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "closed";
            case 5:
                label = "active";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
