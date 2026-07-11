public class GenMissingBreakBug145 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
            case 2:
                label = "archived";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "active";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
