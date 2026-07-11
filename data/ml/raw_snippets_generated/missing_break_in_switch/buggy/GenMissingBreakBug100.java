public class GenMissingBreakBug100 {
    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "archived";
            case 4:
                label = "paid";
                break;
            case 5:
                label = "expired";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
