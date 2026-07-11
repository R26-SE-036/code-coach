public class GenWhileNoUpdateFix130 {
    static void pump(boolean armed, int count) {
        while (!armed) {
            System.out.println(count);
            count++;
            armed = count > 10;
        }
    }
}
