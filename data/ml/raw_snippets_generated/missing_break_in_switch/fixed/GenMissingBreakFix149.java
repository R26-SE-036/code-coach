public class GenMissingBreakFix149 {
    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
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
                label = "active";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
