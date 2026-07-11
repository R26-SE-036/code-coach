public class GenCleanGeneric058 {
    static boolean isEven1(int attempts) {
        return attempts % 2 == 0;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
