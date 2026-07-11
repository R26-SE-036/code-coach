public class GenMissingBreakBug003 {
    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "final";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static boolean isEven1(int points) {
        return points % 2 == 0;
    }
}
