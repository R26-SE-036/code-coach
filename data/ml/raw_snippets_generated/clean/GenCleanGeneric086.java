public class GenCleanGeneric086 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static boolean isEven2(int points) {
        return points % 2 == 0;
    }
}
