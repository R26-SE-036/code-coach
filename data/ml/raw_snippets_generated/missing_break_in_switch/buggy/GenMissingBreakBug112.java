public class GenMissingBreakBug112 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "closed";
            case 3:
                label = "expired";
                break;
            case 4:
                label = "shipped";
                break;
            case 5:
                label = "draft";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
