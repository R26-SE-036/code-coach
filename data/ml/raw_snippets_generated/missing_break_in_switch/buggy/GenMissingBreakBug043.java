public class GenMissingBreakBug043 {
    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "new";
            case 4:
                label = "archived";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
