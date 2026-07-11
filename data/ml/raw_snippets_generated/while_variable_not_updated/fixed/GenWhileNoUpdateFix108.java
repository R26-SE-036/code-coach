public class GenWhileNoUpdateFix108 {
    static void pump(boolean active, int total) {
        while (!active) {
            System.out.println(total);
            total++;
            active = total > 10;
        }
    }
}
