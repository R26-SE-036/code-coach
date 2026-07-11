public class GenMissingBreakBug119 {
    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
            case 2:
                label = "final";
                break;
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "expired";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
