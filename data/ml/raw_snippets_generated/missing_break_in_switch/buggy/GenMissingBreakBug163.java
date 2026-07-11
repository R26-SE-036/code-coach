public class GenMissingBreakBug163 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "draft";
            case 3:
                label = "archived";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
