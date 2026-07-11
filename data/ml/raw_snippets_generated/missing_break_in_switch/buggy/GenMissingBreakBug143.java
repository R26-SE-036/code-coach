public class GenMissingBreakBug143 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "draft";
                break;
            case 4:
                label = "active";
            case 5:
                label = "shipped";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
